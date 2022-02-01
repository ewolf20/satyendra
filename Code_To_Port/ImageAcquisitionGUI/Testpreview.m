vid=videoinput('winvideo',1);
vidRes = vid.VideoResolution; 
nBands = vid.NumberOfBands; 
ax=axes();
hImage = image( zeros(vidRes(2), vidRes(1), nBands),'Parent',ax );
preview(vid, hImage); 
set(ax,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]) ;