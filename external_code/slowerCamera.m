classdef slowerCamera < handle
    %MEASUREMENT
    properties
        settings = struct;
        hardware = struct;
    end
    
    methods
        function this = slowerCamera(varargin)
            p = inputParser;
            
            p.addParameter('PauseTime',0);
            p.addParameter('cameraType','AtomShutter');
            p.parse(varargin{:});
            this.settings.pause              = p.Results.PauseTime;
            this.settings.cameraType         = p.Results.cameraType;
            
            if strcmp(this.settings.cameraType,'AtomShutter')
                this.hardware.camera             = webcam(2);
%                 this.hardware.camera.Saturation  = 128;
%                 this.hardware.camera.Contrast    = 80;
%                 this.hardware.camera.Brightness  = 140;
                this.settings.marqueeBox         = [924   380    80    44];
            else
                this.settings.marqueeBox         = [982   457    83    13];
                this.hardware.camera             = webcam(2);
                this.hardware.camera.Saturation  = 128;
                this.hardware.camera.Contrast    = 80;
                this.hardware.camera.Brightness  = 140;
                %this.hardware.camera.WhiteBalanceMode = 'auto';
            end
            
            this.settings.previewBox         = [333           3        1251        1053];
            this.settings.pause              = 0;
            this.measureCounts;
        end
        
        function setNewMarqueeBox(this)
            myImg = flipud(snapshot(this.hardware.camera));
            figure(992),clf;
            imshow(myImg);
            this.settings.marqueeBox = round(getrect);
            this.measureCounts;
        end
        
        function measureCounts(this)
            ButtonHandle = figure(991);
            ButtonHandle.Position = [ButtonHandle.Position(1),ButtonHandle.Position(2),120,50];
            
            H = uicontrol('Style', 'PushButton', ...
                                'String', 'Stop', ...
                                'Callback', 'delete(gcbf)');
            
            
            counts = [];
            time = [];
            t = tic;
            
            while ishandle(H)
                time = [time;toc(t)];
                myImg = flipud(snapshot(this.hardware.camera));
                
                %previewImg = myImg(this.settings.previewBox(2):this.settings.previewBox(2)+this.settings.previewBox(4),this.settings.previewBox(1):this.settings.previewBox(1)+this.settings.previewBox(3));
                %figure(991);
                subplot(2,1,1);
                imagesc((myImg));
                hold on
                axis off
                [imageHeight,imageWidth] = size(myImg);
                rectangle('Position',[this.settings.marqueeBox(1),this.settings.marqueeBox(2),this.settings.marqueeBox(3),this.settings.marqueeBox(4)],...
                'EdgeColor','r','LineWidth',1.5,'LineStyle','-')
                hold off
                
                
                regionOfInterest = myImg(this.settings.marqueeBox(2):this.settings.marqueeBox(2)+this.settings.marqueeBox(4),this.settings.marqueeBox(1):this.settings.marqueeBox(1)+this.settings.marqueeBox(3));
                
                counts(end+1) = sum(sum(regionOfInterest));
                subplot(2,1,2);
                plot(time,counts)
                title(num2str(counts(end)))
                xlabel('seconds')
                ylabel('Counts')
                drawnow;
                pause(this.settings.pause);
                
            end
        end
    end
    
end