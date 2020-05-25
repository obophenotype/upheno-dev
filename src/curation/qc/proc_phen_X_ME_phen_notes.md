Analysis of process/material entity phenotype tangles in MP.

PROBE:
('has part' some ('inheres in part of' some 'material entity')) 
and 
('has part' some  ('inheres in part of' some biological_process))

=>  3341 classes

Many of these appear to be developmental process mixed with terminal phenotypes affecting anatomical entities: 
('has part' some ('inheres in part of' some 'material entity'))
and
('has part' some  ('inheres in part of' some 'developmental process'))

=> 1129 classes


('has part' some ('inheres in part of' some 'material entity')) and ('has part' some  ('inheres in part of' some pigmentation))

has [114 classes](https://gist.github.com/dosumis/94160cb409ec0f7d4e0a37472b2cfdd7#file-mel_phenotype_x_pigmentation_proc)

'abnormal homeostasis' and ('has part' some ('inheres in part of' some 'material entity')) = 1081 classes!


Some dodgy axiomatization of high-level terms account for much of the tangle:

'abnormal cell physiology': 'has part' some 
    (functionality
     and ('inheres in' some cell)
     and ('has modifier' some abnormal))
     

This pattern is repeated for a whole class of terms:

e.g. 
'abnormal immue cell physiology':
'has part' some 
    (functionality
     and ('inheres in' some cell)
     and ('inheres in part of' some 'immune system')
     and ('has modifier' some abnormal))
    
'abnormal immune system physiolgy': 'has part' some 
    (functionality
     and ('inheres in' some 'immune system')
     and ('has modifier' some abnormal))
     
'cellular phenotype' manually classified many cell process phenotypes, but has the logical definition:

'has part' some 
    (quality
     and ('inheres in' some cell))
