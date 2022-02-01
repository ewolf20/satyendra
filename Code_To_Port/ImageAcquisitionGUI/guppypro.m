%Initialize
    vid = videoinput('gentl', 1, 'Mono8');
    src = getselectedsource(vid);
    triggerconfig(vid, 'hardware', 'DeviceSpecific', 'DeviceSpecific');
    src.ExposureStartTriggerActivation = 'RisingEdge';
    src.ExposureStartTriggerMode = 'On';
    vid.ROIPosition = [0 0 2588 1940];
    % TriggerRepeat is zero based and is always one
    % less than the number of triggers.
    vid.TriggerRepeat = 3;
    vid.FramesPerTrigger=1;
    vid.Timeout=10000;
    src.ExposureAuto = 'Off';
    src.ExposureTime = 508;
    figure;
    interrupt='No';
    
while isequal(interrupt,'No')
    start(vid);
    pwa=getsnapshot(vid);
    disp(vid.FramesAcquired);
    pwoa=getsnapshot(vid);
    disp(vid.FramesAcquired);
    df=getsnapshot(vid);
    disp(vid.FramesAcquired);
    absorb=(pwa-df)./(pwoa-df);
    imagesc(absorb);
    interrupt = questdlg('Do you want to interrupt the acquisition?', ...
	'Yes', ...
	'No');
end

delete(vid)
clear vid; clear src
delete(imaqfind)

 