function updateshow( handles )
if not(all(size(handles.currentimage)==size(handles.currentmark)))
    set(handles.Markinmain,'Value',0);
end
if get(handles.Markinmain,'Value')
    marker=uint8(handles.currentmark);
    Res=size(handles.currentimage);
    inversemarker=zeros(Res(1),Res(2),3,'uint8');
    inversemarker(:,:,1)=uint8(not(marker(:,:)));
    inversemarker(:,:,2)=uint8(not(marker(:,:)));
    inversemarker(:,:,3)=uint8(not(marker(:,:)));
    org(:,:,1)=uint8(handles.currentimage);
    org(:,:,2)=uint8(handles.currentimage);
    org(:,:,3)=uint8(handles.currentimage);
    markeddata=org.*inversemarker;
    redmarker=zeros(Res(1),Res(2),3,'uint8');
    redmarker(:,:,1)=marker*255;
    imageshow=markeddata+redmarker;
    if get(handles.CMDirect,'Valcolue')
        image(imageshow,'Parent',handles.axes1,'CDataMapping','direct');
    end
    if get(handles.CMRescale,'Value')
        image(imageshow,'Parent',handles.axes1,'CDataMapping','scaled');
    end
else
    imageshow=handles.currentcrop;
    if get(handles.CMDirect,'Value')
        image(imageshow,'Parent',handles.axes1,'CDataMapping','direct');
        colormap(handles.axes1,gray(256));
    end
    if get(handles.CMRescale,'Value')
        image(imageshow,'Parent',handles.axes1,'CDataMapping','scaled');
        colormap(handles.axes1,gray(256));
    end
    if get(handles.CMCustom,'Value')
        min=str2num(get(handles.CMMin,'string'));
        max=str2num(get(handles.CMMax,'string'));
        image(imageshow,'Parent',handles.axes1,'CDataMapping','scaled');
        colormap(handles.axes1,gray(256));
        caxis(handles.axes1,[min max]);
    end
end

set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]) ;
end

