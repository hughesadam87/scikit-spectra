Getting Started
===============

The following sections will provide a brief introduction to the PyCD framework, with a more thorough tutorial coming soon.  First, the basic data containers will be discussed, followed by direct and from-file instantiation.  Utilities for batch domain analysis are presented followed by integration with `BioPython's Seq. class`_.

.. _BioPython's Seq. class: http://biopython.org/DIST/docs/api/Bio.Seq.Seq-class.html


Data Storage: The (Conserved Domains Database) CDD Class
--------------------------------------------------------

For now, the main data container is a class called the **DomainCDD** class.  This is an immutable record class that is created from my `pyrecords project`_.  Essentially, it is a named tuple with extra functionality.   Although this is currently immutble, I may supplant this with a mutable object type in the future.  The choice to choose an immutable record was mainly because these take up very little space in memory and are easy to work with.  
　
.. _pyrecords project: http://hugadams.github.com/pyrecords

Data Fields
-----------

The CDD class supports output from the CD-Batch search tool.  If a user uploads a set of protein sequences, the domains within the sequence are returned.  Here is some output from a real cdd file:

**Q#3** **-** **>SPU_018904**	**superfamily**	**208873**	**361**	**413**	**2.00744e-22**	**97.2737**	**cl08327**	**Glyco_hydro_47** **superfamily**	**C**	 **-**

This record contains 14 delimited fields.  The CDD class stores them in the following 14 attributes.  


**Query** - Refers back to the protein to which the current domain belong.  Referencing by the numerical order proteins were input to the batch cd-search.  For example Q#10 means the current domain belongs to the tenth protein entered in the batch.

**u1** - N/A

**Accession** - GI Accession number `of the protein` to which this domain belongs.  (Note, '>' is stripped internally to be compatible with BioPython Sequence class). 

**Hittype** - Describes an NCBI CDD parameter which more or less corresponds to the extent of curation in the database.  Specific hits, for example, are hand-aligned; whereas, the designation of *superfamily* generally is applied to computationally recognized sequences.  Refer to the `NCBI CDD`_ for a better explanation.

.. _NCBI CDD: http://www.ncbi.nlm.nih.gov/Structure/cdd/cdd.shtml

**PSSMID** - Unique integer identifier for a CD domain.

**Start** - Position along the peptide sequence at which the domain begins.

**End** - Position along the peptide sequence at which the domain ends.

**Eval** - Evalue score for domain identification.  Again, more information on how this is computed is available through `NCBI CDD`_. 

**Score** - Heuristic score of domain match.

**DomAccession** - Accession corresponding to the domain (not protein accession).  cl02432 is the domain accession for c-type lectin domain. 

**DomShortname** - Unique short name corresponding to the domain accession.  E.g. CLECT is the shortname to the c-type lectin domain.

**Matchtype** - Not sure how this is different from hit type at the moment.

**u2**  - N/A

**u3**  - N/A

**sequence** - *New* reserved slot to store the sequence corresponding to the region along the protein to which the domain identifies.  This is not implicitly returned by the NCBI CD Search tool for whatever reason.

Reading in Domains
------------------

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


























　

　

　
