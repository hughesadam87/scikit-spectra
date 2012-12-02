Getting Started
===============

The following sections will provide a brief introduction to the pyuvvis framework, with a more thorough tutorial coming soon.  First, the basic data structure and IO will be discussed, followed by an introduction to basic analysis tools, and then followed by advanced analysis tools.  Basic familiarty with ``pandas`` is assumed, so I'd urge newcomers to run through the tutorial http://pandas.pydata.org/pandas-docs/dev/dsintro.html.

As a firm believer of lead-by example, let's start by loading in some spectral data, and discuss the data structures as we go.

``pyuvvis`` comes with some builtin package data.  This can be accessed easily using a special module called pkgutil.  We are going to load in a serialized set of spectral data from the package
directory, **pyuvvis/data/example_data**.

.. sourcecode:: ipython

   In [8]: import pkgutil

   In [9]: data=pkgutil.get_data('pyuvvis', 'data/example_data/spectra.pickle')

This is a serialized dataframe with custom attributes.  To serialize and deserialize a dataframe without losing specially attached attributes, pyuvvis comes with some custom utilities.
We can load this serialized stream into a dataframe with these as such:


.. sourcecode:: ipython
   
   In [3]: from pyuvvis.pandas_utils.dataframeserial import df_loads

   In [4]: df=df_loads(data)

   In [5]: df
   Out[5]: 
   <class 'pandas.core.frame.DataFrame'>
   Index: 2048 entries, 339.09 to 1023.65
   Columns: 216 entries, 2012-02-03 18:06:46 to 2012-02-04 05:05:56
   dtypes: float64(216)

``df`` corresponds to spectral data with wavelengths from the range 339.09 to 1023.65 nm.  The columns are timestamps ranging from starting around 6pm on Feb 03 2012 and ending around 5am Feb 04 2012.

.. sourcecode:: ipython

   In [6]: df.index
   Out[6]: Index([339.09, 339.48, 339.86, ..., 1023.08, 1023.36, 1023.65], dtype=object)

   In [7]: df.columns[0], df.columns[-1]
   Out[7]: (<Timestamp: 2012-02-03 18:06:46>, <Timestamp: 2012-02-04 05:05:56>)


First, let's explore this dataset using some native pandas features.  

Manipulation with pandas
------------------------

The 














Data Storage: The Pandas Dataframe
----------------------------------

The pandas_ DataFrame class provides is naturally suited to handle spectral data.  We chose the following canonical axis labels:

   1. The column (axis=0) labels are taken to be timepoints for each curve.
   2. The index/rows labels are taken to be the wavelengths/spectral data.  







This powerful and flexible class ensures robust and intuitive data manipulation capabilities, as will be demonstrated in this tutorial.  There are some caveats to this that must be kept in mind.  

.. _pandas: http://pandas.pydata.org/


ADD DISCUSSION AFTER ADDING MORE GENERAL MODULES



Manual Instantiation
^^^^^^^^^^^^^^^^^^^^

Let's see how it easy it is to instantiate a CD Domain object.  First, I'm going to demonstrate a manual instantiation; however, in practice, almost all input will be from batch files.  This input style is explained in the `pyrecords project`_ more thoroughly.  Records are generated first by inputing the immutable manager class, in this case, it is called *domain_manager*.

.. sourcecode:: ipython

   In [2]: from DataTypes.cdd_fields import domain_manager

Taking my example string:

**Q#3** **-** **>SPU_018904**	**superfamily**	**208873**	**361**	**413**	**2.00744e-22**	**97.2737**	**cl08327**	**Glyco_hydro_47** **superfamily**	**C**	 **-**

I will pass this as a list into the domain_manager.  This is very similar to namedtuple syntax, but pyrecords is automatically converts all of the attributes to their proper types.  For example, the attribute *Start* will be converted into an integer by default.

.. sourcecode:: ipython

   In [9]: fake_domain=fake_domain.strip().split()

   In [10]: domain=domain_manager._make(fake_domain, extend_defaults=True)
   In [11]: domain

   Out[11]: DomainCDD(Query='Q#3', u1='-', Accession='>SPU_018904', Hittype='superfamily', PSSMID=208873, Start=361, End=413, Eval=2.00744e-22, Score=97.2737, DomAccession='cl08327', DomShortname='Glyco_hydro_47', Matchtype='superfamily', u2='C', u3='-', sequence='')

Now I have complete attribute access with the correct field types.  

.. sourcecode:: ipython

   In [13]: domain.Accession, domain.Score
   Out[13]: ('>SPU_018904', 97.2737)

   In [15]: type(domain.Accession), type(domain.Score) 
   Out[15]: (str, float)

Anyone who is familiar with Python's *namedtuple* data containers should find this syntax familiar.

File Input
^^^^^^^^^^

For now, he batch output of NCBI's CD Search is the only filetype supported.  It should be straigtforward to create custom file input shcemes, as the file reader function, *from_cdd_file()* is merely a small wrapper around the pyrecords *from_file()* function.  To demonstrate, I will load in a Test set of 500 real purple sea urchin proteins.

.. sourcecode:: ipython

   In [11]: domains=from_cdd_file(domain_manager, 'TestData/TestSet.txt')
   In [13]: domains[0]

   Out[13]: DomainCDD(Query='Q#1', u1='-', Accession='>WHL22.684570.0', Hittype='superfamily', PSSMID=212227, Start=189, End=410, Eval=2.91122e-33, Score=124.196, DomAccession='cl00489', DomShortname='60KD_IMP', Matchtype='superfamily', u2='-', u3='-', sequence='')

Domain Analysis
---------------

The following sections will demonstrate some of the ways to manipulate and analyze batches of CD domains in PyCD.

Manipulating Data
^^^^^^^^^^^^^^^^^

PyRecords's *to_dic()* function allows for very flexible dictionary recasting right out of the box.  *to_dic()* requires the user specify an attribute field to key the dictionary.  If we wanted to key the dictionary by, for example, the unique integer PSSMID, this is very simple:


.. sourcecode:: ipython

   In [16]: domdic=to_dic(domains, 'PSSMID')
   In [18]: domdic.items()[0]

   Out[18]: (199168, DomainCDD(Query='Q#174', u1='-', Accession='>WHL22.399623.0' ...))

In reality, the PSSMID **is not** a good key because the same domains appear multiple times in the data set.  Therefore, this key **is not unique**.  *to_dic()* makes it quite easy to create custom dictionary keys as a composition of field attribtues.  For example, the datafields *Accession*, *Start*, *End*, *PSSMID* together make a key that is both unique and informative.  This is easy to implement.

.. sourcecode:: ipython

   In [22]: domdic=to_dic(domains, 'Accession', 'Start', 'End', 'PSSMID')
   In [23]: domdic.items()[0]

   Out[23]: ('>WHL22.485427.0_497_567_209363', DomainCDD(Query='Q#391', u1='-', Accession='>WHL22.485427.0' ...))

It doesn't matter that the *Start* and *End* fields were stored as integers; *to_dic()* recasts them to strings.  The default delimiter used to separate attribute fields is the underscore, '_', and be changed via a keyword parameter in the function call.

A second way to store batch data is in the **formatted domains** style, which assigns domains to their respective proteins in a manner which preserves order.  The domains will be recorded by their domain accessions by defaults (e.g. "cl02432"); however, they may be stored via shortname (e.g. "CLECT") through a keyword in the *formatted_domains()* function call:

.. sourcecode:: ipython

   In [27]: acs=formatted_domains(domains)
   In [28]: shorts=formatted_domains(domains, style='Domain Shortname')

   In [32]: acs.items()[1]
   Out[32]: ('>WHL22.437786.0', ['cl02608', 'cl00158', 'cl03218', 'cl15779'])

   In [35]: shorts.items()[1] 
   Out[35]: ('>WHL22.437786.0', ['BAH', 'ZnF_GATA', 'ELM2', 'SANT'])


This formatted_domains representation is more natural for visualizing how the domains are structured along the proteins.  In summary, there are three distinct ways to store batch domain data in PyCD:

1. Nested tuples is the default storage style of PyCD and is returned by the *from_cdd_file()* function.
2. Dictionaries with unique composite attribute keys is another useful way to handle the data.
3. The so-called *formatted domains* style retains information about domain ordering along a protein.  

Often times, one representation of the dataset is more natural for a given type of analysis as will be demonstrated below.  As PyCD matures, a dataclass may be assigned to the formatted domains storage style to include additional domain information such as position along a protein and other information.

Analysis
^^^^^^^^

PyRecords offers a general *histogram()* function to count attribute value occurrences in the set; for now this is built to handle dictionary input, but soon will handle nested tuples as well.  A call to this function specifying either of the domain attribute fields results in the domain distribution for the dataset:

.. sourcecode:: ipython

   In [43]: hist=histogram(domdic, 'DomAccession', sorted_return=True)

   In [44]: hist['DomAccession'][0:3]
   Out[44]: (('cl09941', 82), ('cl11960', 43), ('cl09099', 27))

If the slice notation of the histogram looks confusing, it is because the *histogram()* function is actually designed to accept multiple input fields.  Hence, multiple histograms can be generated simultaneously across attribute fields.  For example, below I will count occurrences for the Domain Acession field and PSSMID field simultaneously, and then output the top three PSSMID results.

.. sourcecode:: ipython

   In [48]: hist=histogram(domdic, 'DomAccession', 'PSSMID', sorted_return=True)
   In [49]: hist['PSSMID'][0:3]

   Out[49]: ((209104, 82), (209398, 43), (212291, 27))

Viewing domain data as a *network* is another important facet of domain analysis.  In the future, I would like to interface PyCD to Python's NetworkX_ package.  For now, I use a custom algorithm to create a network from the domain data.  This is done through the *network_diagram()* function and requires the formatted domains style of input.  It is important to emphasize that *network_diagram()* *does not* make a full network for entire dataset; rather, it creates a network for a single domain in the set.   A root domain (node) must be passed in the function call:

.. _NetworkX: http://networkx.lanl.gov/


.. sourcecode:: ipython

   In [51]: shorts=formatted_domains(domains, style='Domain Shortname')
   In [57]: domain_net=network_diagram(shorts, 'TPR')

   In [58]: domain_net
   Out[58]: Network(seed_domain='TPR', flank_left=('CHAT',), flank_right=(), singles=3, doubles=13, n_terminal=3, c_terminal=3)

The information above indicates which domains are found adjacent to TPR in mosaic (multi-domain) proteins.  Only the CHAT domain appears with TPR; otherwise, TPR is found either along, or in pairs (13 times this happens).  This function will likely be supplanted by more sophisticated utilities after interfacing to NetworkX.  For now, it is useful to our analysis.

PyCD provides a *network_outfile()* function that outputs the network data as a summary as well as an *adjacency matrix*.  The adjacency matrix output is a standard format for network visualization tools like the stellar yEd_ software.

.. _yEd: http://www.yworks.com/en/products_yed_about.html

The output of *network_outfile()*, when read in directly to yEd_ (after tweaking a bit of yEd's options), yields the following plot using CLECT as a root node in an entire computationally-annotated proteome:

.. image:: Tutorial_images/clect_adj.bmp

Integration with BioPython Seq. Class
-------------------------------------

A special *sequence* field is reserved in the Domains CDD class for the protein sequence of an identified domain.  Although the NCBI CDD tool returns the *start* and *end* points along a sequence, it does not retain this information in the results.  Therefore, it is quite helpful to be able to reassign these, especially for downstream analysis like performing phylogenetics and sequence alignment on the identified domains.  

Again, we will read in domains from a file.

.. sourcecode:: ipython

   In [73]: domains=from_cdd_file(domain_manager, 'TestData/TestSet.txt', warning=False)  
   In [74]: domains[0]

   Out[74]: DomainCDD(Query='Q#1', u1='-', Accession='>WHL22.684570.0'...)

Now, we will read in a set of protein sequences using the *proteins_from_file()* function, which is merely a small wrapper for the *SeqIO.parse()* method of the in `BioPython Seq class`_.  

.. _BioPython Seq class: http://biopython.org/DIST/docs/api/Bio.Seq.Seq-class.html

.. sourcecode:: ipython

   In [77]: proteins[0]
   
   Out[77]: SeqRecord(seq=Seq('MYHPACRPASLARFQRGLHSAVFNPKTSLQQGASCSSHHHGALSDRQHIDSRKH...TDL', ProteinAlphabet()), id='WHL22.684570.0', name='WHL22.684570.0', description='WHL22.684570.0 [86 - 1501]', dbxrefs=[])

It is important to realize that BioPython sequences crop the '>' character from the Accession of a protein sequence.  To match this, we must envoke the *crop_accession()* function.


In [79]: domains=crop_accession(domains)
In [80]: domains[0].Accession

Out[81]: 'WHL22.684570.0'

*crop_accession()* is a small wrapper around a powerful pyrecords function, *alter_field*, which lets the user specify a field and function.  The function is then applied to all field members.  For *crop_accession()*, one merely is passing the string method, .strip('>'), to the field attribute 'Accession'.  The full call signature is shown below:

.. sourcecode::
    domains=[alter_field(domain, 'Accession', lambda x: x.strip('>') ) for domain in domains]

Finally, we can assign the peptide sequence to the CDD domains batch.

.. sourcecode:: ipython

   In [83]: domains=assign_dom_seq(domains, proteins)
   In [85]: domains[0].Start, domains[0].End, domains[0].sequence

   Out[85]: (189, 410, Seq('WATVVATTFTLRFSLTLPLAIYSQNIRVRVENLQPEVIALAKRSFVERFAARAK...KIP', ProteinAlphabet()))


























　

　

　
