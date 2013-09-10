


# Makes report basically from main outfile
template_main = file('template/experiment_main.tex', 'r').read()

# Don't forget the fulldoc
main_params = {'title': 'FOO TITLE', 
          'author':'Adam Hughes', 
          'email':'hugadams@gwmail.gwu.edu', 
                }



# main_params.update
page = template % main_params

# report name (should default to name infolder)
open('test.tex', 'w').write(page)


    


#\section{Analysis}
#Root indirectory: %(inroot)s
#Root outdirectory: %(outroot)s