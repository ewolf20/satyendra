function varargout = MarkToolbox(varargin)
% MARKTOOLBOX MATLAB code for MarkToolbox.fig
%      MARKTOOLBOX, by itself, creates a new MARKTOOLBOX or raises the existing
%      singleton*.
%
%      H = MARKTOOLBOX returns the handle to a new MARKTOOLBOX or the handle to
%      the existing singleton*.
%
%      MARKTOOLBOX('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in MARKTOOLBOX.M with the given input arguments.
%
%      MARKTOOLBOX('Property','Value',...) creates a new MARKTOOLBOX or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before MarkToolbox_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to MarkToolbox_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help MarkToolbox

% Last Modified by GUIDE v2.5 08-Jan-2015 16:14:48

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @MarkToolbox_OpeningFcn, ...
                   'gui_OutputFcn',  @MarkToolbox_OutputFcn, ...
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


% --- Executes just before MarkToolbox is made visible.
function MarkToolbox_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to MarkToolbox (see VARARGIN)


handles.hMainGui=getappdata(0,'hMainGui');
handles.currentimage=getappdata(handles.hMainGui,'CurrentImage');
setappdata(handles.hMainGui,   'Wait'    , 1);
handles.folder=getappdata(handles.hMainGui,'Path');
%remove inf and nan in image
infpoints = handles.currentimage == Inf;
handles.currentimage(infpoints) = 0;
infpoints = handles.currentimage == -Inf;
handles.currentimage(infpoints) = 0;
nanpoints = isnan(handles.currentimage);
handles.currentimage(nanpoints) = 0;

handles.currentcrop=handles.currentimage;
handles.pos=[1,size(handles.currentimage,2),1,size(handles.currentimage,1)];
handles.currentmark=0;
handles.ifmark=0;
handles.binary=0;
handles.max=max(handles.currentimage(:));
handles.min=min(handles.currentimage(:));

imagesc(handles.currentcrop,'Parent',handles.axes1);
colormap(handles.axes1,gray(256));
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);

% Choose default command line output for MarkToolbox
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes MarkToolbox wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = MarkToolbox_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;


% --- Executes on slider movement.
function slider2_Callback(hObject, eventdata, handles)
% hObject    handle to slider2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider
thres=get(hObject,'Value');
thres=(handles.max-handles.min)*thres+handles.min;
if not(get(handles.Invs,'Value'))
    I=(handles.currentcrop>thres);
else
    I=(handles.currentcrop<=thres);
end
imagesc(I,'Parent',handles.axes1);
colormap(handles.axes1,gray(256));
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);
handles.binary=I;
guidata(hObject,handles);

% --- Executes during object creation, after setting all properties.
function slider2_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end


% --- Executes on button press in Invs.
function Invs_Callback(hObject, eventdata, handles)
% hObject    handle to Invs (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of Invs


% --- Executes on button press in Outline.
function Outline_Callback(hObject, eventdata, handles)
% hObject    handle to Outline (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

%find the outline
B = bwboundaries(handles.binary);
%find the longies out line
NB=size(B,1);
maxlength=0;
j=0;
for i=1:NB
    if (size(B{i},1)>maxlength)
        maxlength=size(B{i},1);
        j=i;
    end    
end
outline=B{j};
%create a outline marker
Nl=size(outline,1);
marker=zeros(size(handles.currentcrop,1),size(handles.currentcrop,2));
for i=1:Nl
    marker(outline(i,1),outline(i,2))=1;
end
imagesc(marker,'Parent',handles.axes1);
fullmarker=zeros(size(handles.currentimage,1),size(handles.currentimage,2));
fullmarker(handles.pos(3):handles.pos(4),handles.pos(1):handles.pos(2))=marker;
handles.mark=fullmarker;
handles.ifmark=1;
guidata(hObject,handles);


% --- Executes on button press in Overlap.
function Overlap_Callback(hObject, eventdata, handles)
% hObject    handle to Overlap (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
bitmap1=(single(handles.currentimage)-single(handles.min))/single(handles.max-handles.min);
bitmap2=(single(handles.currentimage)-single(handles.min))/single(handles.max-handles.min);
A=handles.mark;
outline=A>0;
bitmap2(outline)=0;
bitmap1(outline)=1;
rgbmap(:,:,1)=bitmap1;
rgbmap(:,:,2)=bitmap2;
rgbmap(:,:,3)=bitmap2;
imagesc(rgbmap,'Parent',handles.axes1);
colormap(handles.axes1,gray(256));
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);


% --- Executes on button press in Save.
function Save_Callback(hObject, eventdata, handles)
% hObject    handle to Save (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
if handles.ifmark
    setappdata(handles.hMainGui,'CurrentMark',handles.mark);
    setappdata(handles.hMainGui,'IfMark',1);
end
setappdata(handles.hMainGui,'Wait',0);
close(handles.figure1);




% --- Executes on button press in Crop.
function Crop_Callback(hObject, eventdata, handles)
% hObject    handle to Crop (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
[image_crop,rect]=imcrop(handles.axes1);
handles.currentcrop=image_crop;

RangeX=size(handles.currentimage,2);
RangeY=size(handles.currentimage,1);
X1=max(round(rect(1)),1);
Y1=max(round(rect(2)),1);
X2=min(round(rect(3))+X1-1,RangeX);
Y2=min(round(rect(4))+Y1-1,RangeY);
handles.pos=[X1 X2 Y1 Y2];

imagesc(handles.currentcrop,'Parent',handles.axes1);
colormap(handles.axes1,gray(256));
set(handles.axes1,'DataAspectRatioMode','manual','DataAspectRatio',[1 1 1]);

guidata(hObject,handles);


% --- Executes when user attempts to close figure1.
function figure1_CloseRequestFcn(hObject, eventdata, handles)
% hObject    handle to figure1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: delete(hObject) closes the figure
setappdata(handles.hMainGui,'Wait',0);
delete(hObject);


% --- Executes on button press in Savefile.
function Savefile_Callback(hObject, eventdata, handles)
% hObject    handle to Savefile (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
[FileName,PathName]=uiputfile([handles.folder,'\','*.fits']);
file=[PathName,FileName];
fitswrite(handles.mark,file);
