function out=SearchDevice()
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
adaptors=imaqhwinfo();
adaptors=adaptors.InstalledAdaptors;
Na=length(adaptors);
out={};
for i=1:Na
    obj=imaqhwinfo(adaptors{i});
    obj=obj.DeviceIDs;
    M=length(obj);
    for j=1:M
        Atemp=adaptors{i};
        ID=obj{j};
        Dinfo=imaqhwinfo(Atemp,ID);
        name=[Dinfo.DeviceName,'-',Atemp,num2str(ID)];
        out=[out;{Atemp,ID,name}];
    end
end

end

