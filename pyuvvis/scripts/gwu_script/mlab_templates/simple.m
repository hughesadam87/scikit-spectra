clear;    
close all; 
clc;clc;  

files = {
%(files)s
};

for i=1:length(files)
    file = files{i};            
    myData.(files{i}) = importdata(file);
    myData.(files{i}).labels = myData.(files{i}).data(:,1);
    myData.(files{i}).data = myData.(files{i}).data(:,2:end);
end

%(attrnames)s