from dataframeserial import _get_metadict

### Following two functions deal with attribute stored of dataframe.
def store_attr(df):
    ''' Store all the attributes in a dataframe that are not found in an empty dataframe
    declared with DataFrame().'''
    return _get_metadict(df)
    
def restore_attr(df, stored_attr):
    ''' Set the attributes of the pandas dataframe using sotred_attr dictionary.'''
    for attr, value in stored_attr.items():
        setattr(df, attr, value)    
    return df

def transfer_attr(df1, df2, reversedeletion=False, speakup=True):
    ''' Transfer all the attributes from df1 to df2.  If none found, returns df2.
    Speakup keyword just adds print statements.
    Reverse deletion means that all attributes in df2 that are not found in df1.'''
    if reversedeletion:
        raise NotImplementedError('Didnt put that option in yet chief.')
    
    df1attr=store_attr(df1)

    if len(df1attr) > 0:
        df2=restore_attr(df2, df1attr)
        if speakup:            
            print '\nTransferring %s attributes:\n'%len(df1attr)        

    else:
        if speakup:
            print 'No attributes found for transfer'
    
    return df2
     

