function varargout = GuppySetting(varargin)
% GUPPYSETTING MATLAB code for GuppySetting.fig
%      GUPPYSETTING, by itself, creates a new GUPPYSETTING or raises the existing
%      singleton*.
%
%      H = GUPPYSETTING returns the handle to a new GUPPYSETTING or the handle to
%      the existing singleton*.
%
%      GUPPYSETTING('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in GUPPYSETTING.M with the given input arguments.
%
%      GUPPYSETTING('Property','Value',...) creates a new GUPPYSETTING or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before GuppySetting_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to GuppySetting_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help GuppySetting

% Last Modified by GUIDE v2.5 08-Jan-2015 19:51:13

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @GuppySetting_OpeningFcn, ...
                   'gui_OutputFcn',  @GuppySetting_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before GuppySetting is made visible.
function GuppySetting_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to GuppySetting (see VARARGIN)

%Get the handle of the video input object from main Gui
handles.hMainGui=getappdata(0,'hMainGui');
handles.currentdevice=getappdata(handles.hMainGui,'DeviceHandle');
src = getselectedsource(handles.currentdevice);

%set all the ExposureTime and Delay Time
set(handles.ExposureTime,'String',num2str(src.ExposureTime));
set(handles.ExposureDelay,'String',num2str(src.ExposureStartTriggerDelay));
a1=log(5*10^5)/1000;
a2=log(2*10^6+1)/1000;
exslider=max(min(log(src.ExposureTime/20)/a1,1000),0);
dlslider=max(min(log(src.ExposureStartTriggerDelay+1)/a2,1000),0);
set(handles.ExposureTimeSlider,'Value',exslider);
set(handles.DelaySlider,'Value',dlslider);

%set the region of interest
maxheight=imaqhwinfo(handles.currentdevice,'MaxHeight');
maxwidth=imaqhwinfo(handles.currentdevice,'MaxWidth');
handles.yrange=maxheight;
handles.xrange=maxwidth;
roi=handles.currentdevice.ROIPosition;
X1=roi(1)+1;
Y1=roi(2)+1;
X2=X1+roi(3)-1;
Y2=Y1+roi(4)-1;
set(handles.X1,'String',int2str(X1));
set(handles.X2,'String',int2str(X2));
set(handles.Y1,'String',int2str(Y1));
set(handles.Y2,'String',int2str(Y2));
set(handles.Ysize,'String',num2str(maxheight));
set(handles.Xsize,'String',num2str(maxwidth));


%set the schematic
sch=zeros(maxheight,maxwidth,3,'single');
sch(:,:,1)=1;
sch(Y1:Y2,X1:X2,1)=0;
sch(Y1:Y2,X1:X2,2)=1;
handles.im=image(sch,'Parent',handles.axes1);
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]) 

src.ExposureAuto = 'Off';
handles.src=src;

%set the binning mode
mode=src.IIDCMode;
var=str2num(mode(5))+1;
set(handles.ModeList,'Value',var);

% Choose default command line output for GuppySetting
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes GuppySetting wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = GuppySetting_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;



function Y1_Callback(hObject, eventdata, handles)
% hObject    handle to Y1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of Y1 as text
%        str2double(get(hObject,'String')) returns contents of Y1 as a double
y1=max(1,round(str2num(get(handles.Y1,'String'))));
y2=min(round(str2num(get(handles.Y2,'String'))),handles.yrange);
x1=max(1,round(str2num(get(handles.X1,'String'))));
x2=min(round(str2num(get(handles.X2,'String'))),handles.xrange);

if ((y2-y1)<64)
    y2=min(y1+64,handles.yrange);
end
roi=[x1-1 y1-1 x2-x1+1 y2-y1+1];
handles.currentdevice.ROI=roi;
pause(0.1);

roi=handles.currentdevice.ROIPosition;
x1=roi(1)+1;
y1=roi(2)+1;
x2=x1+roi(3)-1;
y2=y1+roi(4)-1;
set(handles.X1,'String',int2str(x1));
set(handles.X2,'String',int2str(x2));
set(handles.Y1,'String',int2str(y1));
set(handles.Y2,'String',int2str(y2));
%set the schematic
sch=zeros(handles.yrange,handles.xrange,3,'single');
sch(:,:,1)=1;
sch(y1:y2,x1:x2,1)=0;
sch(y1:y2,x1:x2,2)=1;
handles.im=image(sch,'Parent',handles.axes1);
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);

guidata(hObject,handles);


% --- Executes during object creation, after setting all properties.
function Y1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to Y1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



function Y2_Callback(hObject, eventdata, handles)
% hObject    handle to Y2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of Y2 as text
%        str2double(get(hObject,'String')) returns contents of Y2 as a double
y1=max(1,round(str2num(get(handles.Y1,'String'))));
y2=min(round(str2num(get(handles.Y2,'String'))),handles.yrange);
x1=max(1,round(str2num(get(handles.X1,'String'))));
x2=min(round(str2num(get(handles.X2,'String'))),handles.xrange);

if ((y2-y1)<64)
    y1=max(y2-64,1);
end
roi=[x1-1 y1-1 x2-x1+1 y2-y1+1];
handles.currentdevice.ROI=roi;
pause(0.1);

roi=handles.currentdevice.ROIPosition;
x1=roi(1)+1;
y1=roi(2)+1;
x2=x1+roi(3)-1;
y2=y1+roi(4)-1;
set(handles.X1,'String',int2str(x1));
set(handles.X2,'String',int2str(x2));
set(handles.Y1,'String',int2str(y1));
set(handles.Y2,'String',int2str(y2));
%set the schematic
sch=zeros(handles.yrange,handles.xrange,3,'single');
sch(:,:,1)=1;
sch(y1:y2,x1:x2,1)=0;
sch(y1:y2,x1:x2,2)=1;
handles.im=image(sch,'Parent',handles.axes1);
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);

guidata(hObject,handles);

% --- Executes during object creation, after setting all properties.
function Y2_CreateFcn(hObject, eventdata, handles)
% hObject    handle to Y2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



function X1_Callback(hObject, eventdata, handles)
% hObject    handle to X1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of X1 as text
%        str2double(get(hObject,'String')) returns contents of X1 as a double
y1=max(1,round(str2num(get(handles.Y1,'String'))));
y2=min(round(str2num(get(handles.Y2,'String'))),handles.yrange);
x1=max(1,round(str2num(get(handles.X1,'String'))));
x2=min(round(str2num(get(handles.X2,'String'))),handles.xrange);

if ((x2-x1)<64)
    x2=min(x1+64,handles.xrange);
end
roi=[x1-1 y1-1 x2-x1+1 y2-y1+1];
handles.currentdevice.ROI=roi;
pause(0.1);

roi=handles.currentdevice.ROIPosition;
x1=roi(1)+1;
y1=roi(2)+1;
x2=x1+roi(3)-1;
y2=y1+roi(4)-1;
set(handles.X1,'String',int2str(x1));
set(handles.X2,'String',int2str(x2));
set(handles.Y1,'String',int2str(y1));
set(handles.Y2,'String',int2str(y2));
%set the schematic
sch=zeros(handles.yrange,handles.xrange,3,'single');
sch(:,:,1)=1;
sch(y1:y2,x1:x2,1)=0;
sch(y1:y2,x1:x2,2)=1;
handles.im=image(sch,'Parent',handles.axes1);
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);

guidata(hObject,handles);

% --- Executes during object creation, after setting all properties.
function X1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to X1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



function X2_Callback(hObject, eventdata, handles)
% hObject    handle to X2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of X2 as text
%        str2double(get(hObject,'String')) returns contents of X2 as a double
y1=max(1,round(str2num(get(handles.Y1,'String'))));
y2=min(round(str2num(get(handles.Y2,'String'))),handles.yrange);
x1=max(1,round(str2num(get(handles.X1,'String'))));
x2=min(round(str2num(get(handles.X2,'String'))),handles.xrange);

if ((x2-x1)<64)
    x1=max(x2-64,1);
end
roi=[x1-1 y1-1 x2-x1+1 y2-y1+1];
handles.currentdevice.ROI=roi;
pause(0.1);

roi=handles.currentdevice.ROIPosition;
x1=roi(1)+1;
y1=roi(2)+1;
x2=x1+roi(3)-1;
y2=y1+roi(4)-1;
set(handles.X1,'String',int2str(x1));
set(handles.X2,'String',int2str(x2));
set(handles.Y1,'String',int2str(y1));
set(handles.Y2,'String',int2str(y2));
%set the schematic
sch=zeros(handles.yrange,handles.xrange,3,'single');
sch(:,:,1)=1;
sch(y1:y2,x1:x2,1)=0;
sch(y1:y2,x1:x2,2)=1;
handles.im=image(sch,'Parent',handles.axes1);
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);

guidata(hObject,handles);

% --- Executes during object creation, after setting all properties.
function X2_CreateFcn(hObject, eventdata, handles)
% hObject    handle to X2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on button press in CropSetting.
function CropSetting_Callback(hObject, eventdata, handles)
% hObject    handle to CropSetting (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
%Prepare the shematic
roi=handles.currentdevice.ROIPosition;
x1=roi(1)+1;
y1=roi(2)+1;
x2=x1+roi(3)-1;
y2=y1+roi(4)-1;
%set the schematic
sch=zeros(handles.yrange,handles.xrange,3,'single');
sch(:,:,1)=1;
sch(y1:y2,x1:x2,1)=0;
sch(y1:y2,x1:x2,2)=1;

h=figure;
d=axes('Parent',h);
image(sch,'Parent',d);
set(d,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);
[image_crop,rect]=imcrop(h);
figure(h);
close(h);
x1=max(round(rect(1)),1);
y1=max(round(rect(2)),1);
x2=min(round(rect(3))+x1-1,handles.xrange);
y2=min(round(rect(4))+y1-1,handles.yrange);

roi=[x1-1 y1-1 x2-x1+1 y2-y1+1];
handles.currentdevice.ROI=roi;
pause(0.1);

roi=handles.currentdevice.ROIPosition;
x1=roi(1)+1;
y1=roi(2)+1;
x2=x1+roi(3)-1;
y2=y1+roi(4)-1;
set(handles.X1,'String',int2str(x1));
set(handles.X2,'String',int2str(x2));
set(handles.Y1,'String',int2str(y1));
set(handles.Y2,'String',int2str(y2));

%Reset the schematic
sch=zeros(handles.yrange,handles.xrange,3,'single');
sch(:,:,1)=1;
sch(y1:y2,x1:x2,1)=0;
sch(y1:y2,x1:x2,2)=1;
handles.im=image(sch,'Parent',handles.axes1);
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);


% --- Executes on slider movement.
function DelaySlider_Callback(hObject, eventdata, handles)
% hObject    handle to DelaySlider (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider
src=handles.src;
var=get(hObject,'Value');
a2=exp(log(2*10^6+1)/1000);
time=round((a2^var)-1);
src.ExposureStartTriggerDelay=time;
pause(0.1);
set(handles.ExposureDelay,'String',num2str(src.ExposureStartTriggerDelay));
guidata(hObject,handles);



% --- Executes during object creation, after setting all properties.
function DelaySlider_CreateFcn(hObject, eventdata, handles)
% hObject    handle to DelaySlider (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end



function ExposureDelay_Callback(hObject, eventdata, handles)
% hObject    handle to ExposureDelay (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of ExposureDelay as text
%        str2double(get(hObject,'String')) returns contents of ExposureDelay as a double
src=handles.src;
time=round(str2num(get(hObject,'String')));
a2=log(2*10^6+1)/1000;
src.ExposureStartTriggerDelay=time;
pause(0.1);
set(handles.DelaySlider,'Value',log(src.ExposureStartTriggerDelay+1)/a2);
guidata(hObject,handles);


% --- Executes during object creation, after setting all properties.
function ExposureDelay_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ExposureDelay (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on slider movement.
function ExposureTimeSlider_Callback(hObject, eventdata, handles)
% hObject    handle to ExposureTimeSlider (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider
src=handles.src;
var=get(hObject,'Value');
a1=exp(log(5*10^5)/1000);
time=round(20*(a1^var));
src.ExposureTime=time;
pause(0.1);
set(handles.ExposureTime,'String',num2str(src.ExposureTime));
guidata(hObject,handles);

% --- Executes during object creation, after setting all properties.
function ExposureTimeSlider_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ExposureTimeSlider (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end



function ExposureTime_Callback(hObject, eventdata, handles)
% hObject    handle to ExposureTime (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of ExposureTime as text
%        str2double(get(hObject,'String')) returns contents of ExposureTime as a double

src=handles.src;
time=round(str2num(get(hObject,'String')));
src.ExposureTime=time;
pause(0.1);
set(handles.ExposureTime,'String',num2str(src.ExposureTime));
a1=log(5*10^5)/1000;
set(handles.ExposureTimeSlider,'Value',log(src.ExposureTime/20)/a1);
guidata(hObject,handles);


% --- Executes during object creation, after setting all properties.
function ExposureTime_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ExposureTime (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes when uipanel1 is resized.
function uipanel1_ResizeFcn(hObject, eventdata, handles)
% hObject    handle to uipanel1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)


% --- Executes on button press in pushbutton3.
function pushbutton3_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)


% --- Executes on selection change in ModeList.
function ModeList_Callback(hObject, eventdata, handles)
% hObject    handle to ModeList (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns ModeList contents as cell array
%        contents{get(hObject,'Value')} returns selected item from ModeList
src=handles.src;
%save the former size of the image
orgwidth=handles.xrange;
orgheight=handles.yrange;
%get the value of the pop up menu
var=get(handles.ModeList,'Value')-1;
newmode=['Mode',num2str(var)];
src.IIDCMode=newmode;
pause(0.1);

mode=src.IIDCMode;
var=str2num(mode(5))+1;
set(handles.ModeList,'Value',var);
% get the factor of magnify
maxheight=imaqhwinfo(handles.currentdevice,'MaxHeight');
maxwidth=imaqhwinfo(handles.currentdevice,'MaxWidth');
handles.yrange=maxheight;
handles.xrange=maxwidth;
kx=maxwidth/orgwidth;
ky=maxheight/orgheight;

% Reset Region of interest 
y1=max(1,round(str2num(get(handles.Y1,'String'))));
y2=min(round(str2num(get(handles.Y2,'String'))),orgheight);
x1=max(1,round(str2num(get(handles.X1,'String'))));
x2=min(round(str2num(get(handles.X2,'String'))),orgwidth);
ny1=max(round((ky-1)*y1),1);
ny2=min(round(ky*y2),maxheight);
nx1=max(round((kx-1)*x1),1);
nx2=min(round(kx*x2),maxwidth);
roi=[nx1-1 ny1-1 nx2-nx1+1 ny2-ny1+1];
handles.currentdevice.ROI=roi;

pause(0.1);
% get the feed back from camera
roi=handles.currentdevice.ROIPosition;
x1=roi(1)+1;
y1=roi(2)+1;
x2=x1+roi(3)-1;
y2=y1+roi(4)-1;
set(handles.X1,'String',int2str(x1));
set(handles.X2,'String',int2str(x2));
set(handles.Y1,'String',int2str(y1));
set(handles.Y2,'String',int2str(y2));
%set the schematic
sch=zeros(handles.yrange,handles.xrange,3,'single');
sch(:,:,1)=1;
sch(y1:y2,x1:x2,1)=0;
sch(y1:y2,x1:x2,2)=1;
handles.im=image(sch,'Parent',handles.axes1);
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);

guidata(hObject,handles);

% --- Executes during object creation, after setting all properties.
function ModeList_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ModeList (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on button press in Close.
function Close_Callback(hObject, eventdata, handles)
% hObject    handle to Close (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% get(handles)
close(handles.figure1);


% --- Executes during object creation, after setting all properties.
function figure1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to figure1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called


% --- Executes when user attempts to close figure1.
function figure1_CloseRequestFcn(hObject, eventdata, handles)
% hObject    handle to figure1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: delete(hObject) closes the figure
delete(hObject);
