# copied from https://gist.github.com/fmassa/c0fbb9fe7bf53b533b5cc241f5c8234c

import typing
from collections import Counter, OrderedDict, defaultdict
from functools import partial, reduce
from itertools import zip_longest

import numpy as np
import torch
import torch.nn as nn
from numpy import prod


def get_shape(val: object) -> typing.List[int]:
    """
    Get the shapes from a jit value object.
    Args:
        val (torch._C.Value): jit value object.
    Returns:
        list(int): return a list of ints.
    """
    if val.isCompleteTensor():  # pyre-ignore
        r = val.type().sizes()  # pyre-ignore
        if not r:
            r = [1]
        return r
    elif val.type().kind() in ("IntType", "FloatType"):
        return [1]
    else:
        print(val.type().kind())

        raise ValueError()


def addmm_flop_jit(
    inputs: typing.List[object], outputs: typing.List[object]
) -> typing.Counter[str]:
    """
    This method counts the flops for fully connected layers with torch script.
    Args:
        inputs (list(torch._C.Value)): The input shape in the form of a list of
            jit object.
        outputs (list(torch._C.Value)): The output shape in the form of a list
            of jit object.
    Returns:
        Counter: A Counter dictionary that records the number of flops for each
            operation.
    """
    # Count flop for nn.Linear
    # inputs is a list of length 3.
    input_shapes = [get_shape(v) for v in inputs[1:3]]
    # input_shapes[0]: [batch size, input feature dimension]
    # input_shapes[1]: [batch size, output feature dimension]
    assert len(input_shapes[0]) == 2
    assert len(input_shapes[1]) == 2
    batch_size, input_dim = input_shapes[0]
    output_dim = input_shapes[1][1]
    flop = batch_size * input_dim * output_dim
    flop_counter = Counter({"addmm": flop})
    return flop_counter


def bmm_flop_jit(inputs, outputs):
    # Count flop for nn.Linear
    # inputs is a list of length 3.
    input_shapes = [get_shape(v) for v in inputs]
    # input_shapes[0]: [batch size, input feature dimension]
    # input_shapes[1]: [batch size, output feature dimension]
    assert len(input_shapes[0]) == 3
    assert len(input_shapes[1]) == 3
    T, batch_size, input_dim = input_shapes[0]
    output_dim = input_shapes[1][2]
    flop = T * batch_size * input_dim * output_dim
    flop_counter = Counter({"bmm": flop})
    return flop_counter


def basic_binary_op_flop_jit(inputs, outputs, name):
    input_shapes = [get_shape(v) for v in inputs]
    # for broadcasting
    input_shapes = [s[::-1] for s in input_shapes]
    max_shape = np.array(list(zip_longest(*input_shapes, fillvalue=1))).max(1)
    flop = prod(max_shape)
    flop_counter = Counter({name: flop})
    return flop_counter


def rsqrt_flop_jit(inputs, outputs):
    input_shapes = [get_shape(v) for v in inputs]
    flop = prod(input_shapes[0]) * 2
    flop_counter = Counter({"rsqrt": flop})
    return flop_counter

def dropout_flop_jit(inputs, outputs):
    input_shapes = [get_shape(v) for v in inputs[:1]]
    flop = prod(input_shapes[0])
    flop_counter = Counter({"dropout": flop})
    return flop_counter

def softmax_flop_jit(inputs, outputs):
    # from https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/profiler/internal/flops_registry.py
    input_shapes = [get_shape(v) for v in inputs[:1]]
    flop = prod(input_shapes[0]) * 5
    flop_counter = Counter({'softmax': flop})
    return flop_counter

def _reduction_op_flop_jit(inputs, outputs, reduce_flops=1, finalize_flops=0):
    input_shapes = [get_shape(v) for v in inputs]
    output_shapes = [get_shape(v) for v in outputs]

    in_elements = prod(input_shapes[0])
    out_elements = prod(output_shapes[0])

    num_flops = (in_elements * reduce_flops
        + out_elements * (finalize_flops - reduce_flops))

    return num_flops


def conv_flop_count(
    x_shape: typing.List[int],
    w_shape: typing.List[int],
    out_shape: typing.List[int],
) -> typing.Counter[str]:
    """
    This method counts the flops for convolution. Note only multiplication is
    counted. Computation for addition and bias is ignored.
    Args:
        x_shape (list(int)): The input shape before convolution.
        w_shape (list(int)): The filter shape.
        out_shape (list(int)): The output shape after convolution.
    Returns:
        Counter: A Counter dictionary that records the number of flops for each
            operation.
    """
    batch_size, Cin_dim, Cout_dim = x_shape[0], w_shape[1], out_shape[1]
    out_size = prod(out_shape[2:])
    kernel_size = prod(w_shape[2:])
    flop = batch_size * out_size * Cout_dim * Cin_dim * kernel_size
    flop_counter = Counter({"conv": flop})
    return flop_counter


def conv_flop_jit(
    inputs: typing.List[object], outputs: typing.List[object]
) -> typing.Counter[str]:
    """
    This method counts the flops for convolution using torch script.
    Args:
        inputs (list(torch._C.Value)): The input shape in the form of a list of
            jit object before convolution.
        outputs (list(torch._C.Value)): The output shape in the form of a list
            of jit object after convolution.
    Returns:
        Counter: A Counter dictionary that records the number of flops for each
            operation.
    """
    # Inputs of Convolution should be a list of length 12. They represent:
    # 0) input tensor, 1) convolution filter, 2) bias, 3) stride, 4) padding,
    # 5) dilation, 6) transposed, 7) out_pad, 8) groups, 9) benchmark_cudnn,
    # 10) deterministic_cudnn and 11) user_enabled_cudnn.
    # PyTorch 1.9 compatiblity
    # assert len(inputs) == 12
    x, w = inputs[:2]
    x_shape, w_shape, out_shape = (
        get_shape(x),
        get_shape(w),
        get_shape(outputs[0]),
    )
    return conv_flop_count(x_shape, w_shape, out_shape)


def einsum_flop_jit(
    inputs: typing.List[object], outputs: typing.List[object]
) -> typing.Counter[str]:
    """
    This method counts the flops for the einsum operation. We currently support
    two einsum operations: "nct,ncp->ntp" and "ntg,ncg->nct".
    Args:
        inputs (list(torch._C.Value)): The input shape in the form of a list of
            jit object before einsum.
        outputs (list(torch._C.Value)): The output shape in the form of a list
            of jit object after einsum.
    Returns:
        Counter: A Counter dictionary that records the number of flops for each
            operation.
    """
    # Inputs of einsum should be a list of length 2.
    # Inputs[0] stores the equation used for einsum.
    # Inputs[1] stores the list of input shapes.
    assert len(inputs) == 2
    equation = inputs[0].toIValue()  # pyre-ignore
    # Get rid of white space in the equation string.
    equation = equation.replace(" ", "")
    # Re-map equation so that same equation with different alphabet
    # representations will look the same.
    letter_order = OrderedDict((k, 0) for k in equation if k.isalpha()).keys()
    mapping = {ord(x): 97 + i for i, x in enumerate(letter_order)}
    equation = equation.translate(mapping)
    input_shapes_jit = inputs[1].node().inputs()  # pyre-ignore
    input_shapes = [get_shape(v) for v in input_shapes_jit]

    if equation == "abc,abd->acd":
        n, c, t = input_shapes[0]
        p = input_shapes[-1][-1]
        flop = n * c * t * p
        flop_counter = Counter({"einsum": flop})
        return flop_counter

    elif equation == "abc,adc->adb":
        n, t, g = input_shapes[0]
        c = input_shapes[-1][1]
        flop = n * t * g * c
        flop_counter = Counter({"einsum": flop})
        return flop_counter

    else:
        raise NotImplementedError("Unsupported einsum operation.")


def matmul_flop_jit(
    inputs: typing.List[object], outputs: typing.List[object]
) -> typing.Counter[str]:
    """
    This method counts the flops for matmul.
    Args:
        inputs (list(torch._C.Value)): The input shape in the form of a list of
            jit object before matmul.
        outputs (list(torch._C.Value)): The output shape in the form of a list
            of jit object after matmul.
    Returns:
        Counter: A Counter dictionary that records the number of flops for each
            operation.
    """
    # Inputs should be a list of length 2.
    # Inputs contains the shapes of two matrices.
    input_shapes = [get_shape(v) for v in inputs]
    assert len(input_shapes) == 2
    assert len(input_shapes[1]) == 2
    assert input_shapes[0][-1] == input_shapes[1][0]
    batch_dim = input_shapes[0][0]
    m1_dim, m2_dim = input_shapes[1]
    flop = m1_dim * m2_dim * batch_dim
    flop_counter = Counter({"matmul": flop})
    return flop_counter


def batchnorm_flop_jit(
    inputs: typing.List[object], outputs: typing.List[object]
) -> typing.Counter[str]:
    """
    This method counts the flops for batch norm.
    Args:
        inputs (list(torch._C.Value)): The input shape in the form of a list of
            jit object before batch norm.
        outputs (list(torch._C.Value)): The output shape in the form of a list
            of jit object after batch norm.
    Returns:
        Counter: A Counter dictionary that records the number of flops for each
            operation.
    """
    # Inputs[0] contains the shape of the input.
    input_shape = get_shape(inputs[0])
    assert 2 <= len(input_shape) <= 5
    flop = prod(input_shape) * 4
    flop_counter = Counter({"batchnorm": flop})
    return flop_counter


def MSDeformAttn_flop_jit(
    inputs: typing.List[object], outputs: typing.List[object]
) -> typing.Counter[str]:
    """
    This method counts the flops for matmul.
    Args:
        inputs (list(torch._C.Value)): The input shape in the form of a list of
            jit object before matmul.
        outputs (list(torch._C.Value)): The output shape in the form of a list
            of jit object after matmul.
    Returns:
        Counter: A Counter dictionary that records the number of flops for each
            operation.
    """
    # 
    # Inputs: 
    #   value (N, Len_in, n_heads, d_model // n_heads),
    #   input_spatial_shapes, input_level_start_index,
    #   sampling_locations (bs, nq, head, lvl, npts, 2),
    # attention_weights, self.im2col_step
    # Outputs: N, C, Nq
    input_shapes = [get_shape(v) for v in inputs]
    assert len(input_shapes) == 5
    # assert len(input_shapes[1]) == 2
    # assert input_shapes[0][-1] == input_shapes[1][0]
    # batch_dim = input_shapes[0][0]
    nq = input_shapes[3][1]
    head, per_head_c = input_shapes[0][2:4]
    # pdb.set_trace()
    n_pts = input_shapes[3][4]

    # m1_dim, m2_dim = input_shapes[1]
    flop = 5 * nq * head * per_head_c * n_pts
    flop_counter = Counter({"MSDeformAttn": flop})
    return flop_counter


# A dictionary that maps supported operations to their flop count jit handles.
_SUPPORTED_OPS: typing.Dict[str, typing.Callable] = {
    "aten::addmm": addmm_flop_jit,
    "aten::_convolution": conv_flop_jit,
    "aten::einsum": einsum_flop_jit,
    "aten::matmul": matmul_flop_jit,
    "aten::batch_norm": batchnorm_flop_jit,
    "aten::bmm": bmm_flop_jit,
    "aten::add": partial(basic_binary_op_flop_jit, name='aten::add'),
    "aten::add_": partial(basic_binary_op_flop_jit, name='aten::add_'),
    "aten::mul": partial(basic_binary_op_flop_jit, name='aten::mul'),
    "aten::sub": partial(basic_binary_op_flop_jit, name='aten::sub'),
    "aten::div": partial(basic_binary_op_flop_jit, name='aten::div'),
    "aten::floor_divide": partial(basic_binary_op_flop_jit, name='aten::floor_divide'),
    "aten::relu": partial(basic_binary_op_flop_jit, name='aten::relu'),
    "aten::relu_": partial(basic_binary_op_flop_jit, name='aten::relu_'),
    "aten::rsqrt": rsqrt_flop_jit,
    "aten::softmax": softmax_flop_jit,
    "aten::dropout": dropout_flop_jit,
    "MSDeformAttn": MSDeformAttn_flop_jit
}

# A list that contains ignored operations.
_IGNORED_OPS: typing.List[str] = [
    "aten::Int",
    "aten::__and__",
    "aten::arange",
    "aten::cat",
    "aten::clamp",
    "aten::clamp_",
    "aten::contiguous",
    "aten::copy_",
    "aten::detach",
    "aten::empty",
    "aten::eq",
    "aten::expand",
    "aten::flatten",
    "aten::floor",
    "aten::full",
    "aten::gt",
    "aten::index",
    "aten::index_put_",
    "aten::max",
    "aten::nonzero",
    "aten::permute",
    "aten::remainder",
    "aten::reshape",
    "aten::select",
    "aten::size",
    "aten::slice",
    "aten::split_with_sizes",
    "aten::squeeze",
    "aten::t",
    "aten::to",
    "aten::transpose",
    "aten::unsqueeze",
    "aten::view",
    "aten::zeros",
    "aten::zeros_like",
    "prim::Constant",
    "prim::Int",
    "prim::ListConstruct",
    "prim::ListUnpack",
    "prim::NumToTensor",
    "prim::TupleConstruct",
]

_HAS_ALREADY_SKIPPED = False


def flop_count(
    model: nn.Module,
    inputs: typing.Tuple[object, ...],
    whitelist: typing.Union[typing.List[str], None] = None,
    customized_ops: typing.Union[
        typing.Dict[str, typing.Callable], None
    ] = None,
) -> typing.DefaultDict[str, float]:
    """
    Given a model and an input to the model, compute the Gflops of the given
    model. Note the input should have a batch size of 1.
    Args:
        model (nn.Module): The model to compute flop counts.
        inputs (tuple): Inputs that are passed to `model` to count flops.
            Inputs need to be in a tuple.
        whitelist (list(str)): Whitelist of operations that will be counted. It
            needs to be a subset of _SUPPORTED_OPS. By default, the function
            computes flops for all supported operations.
        customized_ops (dict(str,Callable)) : A dictionary contains customized
            operations and their flop handles. If customized_ops contains an
            operation in _SUPPORTED_OPS, then the default handle in
             _SUPPORTED_OPS will be overwritten.
    Returns:
        defaultdict: A dictionary that records the number of gflops for each
            operation.
    """
    # Copy _SUPPORTED_OPS to flop_count_ops.
    # If customized_ops is provided, update _SUPPORTED_OPS.
    flop_count_ops = _SUPPORTED_OPS.copy()
    if customized_ops:
        flop_count_ops.update(customized_ops)

    # If whitelist is None, count flops for all suported operations.
    if whitelist is None:
        whitelist_set = set(flop_count_ops.keys())
    else:
        whitelist_set = set(whitelist)

    # Torch script does not support parallell torch models.
    if isinstance(
        model,
        (nn.parallel.distributed.DistributedDataParallel, nn.DataParallel),
    ):
        model = model.module  # pyre-ignore

    assert set(whitelist_set).issubset(
        flop_count_ops
    ), "whitelist needs to be a subset of _SUPPORTED_OPS and customized_ops."
    assert isinstance(inputs, tuple), "Inputs need to be in a tuple."

    # Compatibility with torch.jit.
    if hasattr(torch.jit, "get_trace_graph"):
        trace, _ = torch.jit.get_trace_graph(model, inputs)
        trace_nodes = trace.graph().nodes()
    else:
        trace, _ = torch.jit._get_trace_graph(model, inputs)
        trace_nodes = trace.nodes()

    skipped_ops = Counter()
    total_flop_counter = Counter()

    # unique_kinds = {node.kind() for node in trace_nodes}
    # print(unique_kinds)
    # pdb.set_trace()
    for node in trace_nodes:
        kind = node.kind()
        # print(kind)
        if kind == 'prim::PythonOp':
            if 'MSDeformAttn' in str(node):
                kind = 'MSDeformAttn'
        if kind not in whitelist_set:
            # print("not in whitelist_set")
            # If the operation is not in _IGNORED_OPS, count skipped operations.
            if kind not in _IGNORED_OPS:
                skipped_ops[kind] += 1
                # print("skipped_ops")
                # pdb.set_trace()
            continue

        handle_count = flop_count_ops.get(kind, None)
        # pdb.set_trace()
 
        if handle_count is None:
            # print("handle_count is None")
            continue

        inputs, outputs = list(node.inputs()), list(node.outputs())
        flops_counter = handle_count(inputs, outputs)
        # pdb.set_trace()
        total_flop_counter += flops_counter

    global _HAS_ALREADY_SKIPPED
    if len(skipped_ops) > 0 and not _HAS_ALREADY_SKIPPED:
        _HAS_ALREADY_SKIPPED = True
        for op, freq in skipped_ops.items():
            pass
            # logging.warning("Skipped operation {} {} time(s)".format(op, freq))

    # Convert flop count to gigaflops.
    final_count = defaultdict(float)
    for op in total_flop_counter:
        final_count[op] = total_flop_counter[op] / 1e9

    return final_count
