rootdir=.
ext=pyc

find $rootdir -iname "*.$ext" -exec rm '{}' ';'

echo "Removal operation complete"

## later make rootdir and ext keywords and put in my path.
## note: if I want it to prompt before deleting each file, 
## find $rootdir -iname "*.$ext" -ok rm '{}' ';'
  
