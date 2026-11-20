import unittest
from scripts.director.text import expand,align
class SpanishNarrationTests(unittest.TestCase):
 def test_original_plain_text_unchanged(self):self.assertEqual(expand('Un texto normal.')[0],'Un texto normal.')
 def test_year_decimal_percent(self):
  text,groups=expand('En 1981, 3,5 y 60%.');self.assertIn('mil novecientos ochenta y uno,',text);self.assertIn('tres coma cinco',text);self.assertIn('sesenta por ciento.',text)
 def test_ambiguous_separator_fails_without_reinterpreting_amount(self):self.assertRaises(ValueError,expand,'Son 1.234 unidades.')
 def test_digit_identifier_keeps_zeroes(self):self.assertEqual(expand('001')[0],'cero cero uno')
 def test_expansion_maps_actual_acoustic_bounds(self):
  words=[{'word':w,'start':i*.2,'end':(i+1)*.2} for i,w in enumerate('En mil novecientos ochenta y uno'.split())]
  mapped=align('En 1981',words);self.assertEqual(mapped[1]['word'],'1981');self.assertAlmostEqual(mapped[1]['start'],.2);self.assertAlmostEqual(mapped[1]['end'],1.2)
 def test_asr_merged_number_is_a_phrase_not_guessed_word_times(self):
  mapped=align('mil novecientos ochenta y uno',[{'word':'1981','start':1.,'end':3.}]);self.assertEqual(mapped,[{'word':'mil novecientos ochenta y uno','start':1.,'end':3.}])
 def test_punctuation_without_phonemes_is_attached(self):
  text,_=expand('Hola — mundo.');self.assertEqual(text,'Hola— mundo.');mapped=align('Hola — mundo.',[{'word':'Hola','start':0,'end':.3},{'word':'mundo.','start':.4,'end':.8}]);self.assertEqual(mapped[0]['word'],'Hola —')
 def test_mismatched_words_are_not_forced(self):self.assertRaises(ValueError,align,'Sesenta minutos',[{'word':'treinta','start':0,'end':.4},{'word':'minutos','start':.5,'end':1}])

 def test_whisper_split_decimal_uses_whole_measured_span(self):
  words=[{'word':'3','start':3.28,'end':3.5},{'word':',5','start':3.5,'end':4.24}]
  self.assertEqual(align('3,5',words),[{'word':'3,5','start':3.28,'end':4.24}])
  words[1]['start']=3.8
  self.assertRaises(ValueError,align,'3,5',words)
 def test_split_decimal_does_not_change_wrong_number(self):
  self.assertRaises(ValueError,align,'3,6',[{'word':'3','start':0.,'end':.2},{'word':',5','start':.2,'end':.5}])
