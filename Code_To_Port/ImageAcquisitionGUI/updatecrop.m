function imgcrop=updatecrop(handles)
% Update the cropped image from given coordinate range
I=0;
if get(handles.CropSelect,'Value') %'selection' crop mode
    I=handles.currentimage;
else %'Crop by coordinate' mode
    X1=round(str2num(get(handles.Xmin,'string')));
    X2=round(str2num(get(handles.Xmax,'string')));
    Y1=round(str2num(get(handles.Ymin,'string')));
    Y2=round(str2num(get(handles.Ymax,'string')));
    [RangeY RangeX]=size(handles.currentimage);
    if (X1<=X2)&&(Y1<=Y2)&&(X1>0)&&(Y1>0)&&(X2<=RangeX)&&(Y2<=RangeY)
        I=handles.currentimage(Y1:Y2,X1:X2);
    else
        warndlg('Image size not available','Warning');  
        I=handles.currentimage;
    end
end
imgcrop=I;
end

