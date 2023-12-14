dataset=$1
   
if [[ $dataset = thumos14 ]];then
    CUDA_VISIBLE_DEVICES=4 python main.py --cfg configs/thumos14_e2e_slowfast_tadtr.yml --eval --resume /home/mdani31/akata-shared/datasets/THUMOS14/thumos_e2e/thumos14_e2e_slowfast_tadtr_reference.pth
else    
    echo "Unsupported dataset ${dataset}. Exit"
fi



