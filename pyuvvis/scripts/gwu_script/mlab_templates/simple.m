clear;    
close all; 
clc;clc;  

files = {
%(files)s
};

basenames = {
%(basenames)s
};

for i=1:length(files)
    file = files{i};            
    myData.(basenames{i}) = importdata(file);
    myData.(basenames{i}).labels = myData.(basenames{i}).data(:,1);
    myData.(basenames{i}).data = myData.(basenames{i}).data(:,2:end);
end

%(attrnames)s