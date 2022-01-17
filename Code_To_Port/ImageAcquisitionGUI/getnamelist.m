function out=getnamelist(devicelist)
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
N=length(devicelist);
out=cell(N);

if N>1
    name=imaqhwinfo(devicelist,'DeviceName');
    ID=get(devicelist,'DeviceID');
    for i=1:N
        out{i}=strcat(strcat(name{i},'-'),num2str(ID{i}));
    end
end

if N==1
    name=imaqhwinfo(devicelist,'DeviceName');
    ID=get(devicelist,'DeviceID');
    out{1}=strcat(strcat(name,'-'),num2str(ID));
end

end

