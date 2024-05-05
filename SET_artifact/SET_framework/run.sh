#! /bin/bash

<<Example
./build/stschedule config/fig-8_ResNet-50_cloud_BS-1_conf.txt > results/fig-8_ResNet-50_cloud_BS-1.txt
./build/stschedule config/fig-8_ResNet-50_edge_BS-1_conf.txt > results/fig-8_ResNet-50_edge_BS-1.txt
./build/stschedule config/fig-8_ResNet-50_cloud_BS-64_conf.txt > results/fig-8_ResNet-50_cloud_BS-64.txt
./build/stschedule config/fig-8_ResNet-50_edge_BS-64_conf.txt > results/fig-8_ResNet-50_edge_BS-64.txt
./build/stschedule config/fig-8_ResNet-50_cloud_BS-8_conf.txt > results/fig-8_ResNet-50_cloud_BS-8.txt
./build/stschedule config/fig-8_ResNet-50_edge_BS-8_conf.txt > results/fig-8_ResNet-50_edge_BS-8.txt
./build/stschedule config/fig-8_GoogLeNet_cloud_BS-1_conf.txt > results/fig-8_GoogLeNet_cloud_BS-1.txt
./build/stschedule config/fig-8_GoogLeNet_edge_BS-1_conf.txt > results/fig-8_GoogLeNet_edge_BS-1.txt
./build/stschedule config/fig-8_GoogLeNet_cloud_BS-64_conf.txt > results/fig-8_GoogLeNet_cloud_BS-64.txt
./build/stschedule config/fig-8_GoogLeNet_edge_BS-64_conf.txt > results/fig-8_GoogLeNet_edge_BS-64.txt
./build/stschedule config/fig-8_GoogLeNet_cloud_BS-8_conf.txt > results/fig-8_GoogLeNet_cloud_BS-8.txt
./build/stschedule config/fig-8_GoogLeNet_edge_BS-8_conf.txt > results/fig-8_GoogLeNet_edge_BS-8.txt
Example

make

for net in 'ResNet-50' 'GoogLeNet'
do
    for scale in 'cloud' 'edge'
    do
        for batch in 1 8 64
        do
            name=fig-8_"$net"_"$scale"_BS-"$batch";
            ./build/stschedule config/"$name"_conf.txt > results/"$name".txt
            # nohup ./build/stschedule config/"$name"_conf.txt > results/"$name".txt &
        done
    done
done