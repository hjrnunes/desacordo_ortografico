#!/usr/bin/env python
# encoding: utf-8
import requests, re, time
from utils.grammar    import Grammar
from utils.settings   import Settings
from utils.exceptions import NoInputGiven
from utils.regexes    import DAO_REGEX, AAO_REGEX, WORDS_REGEX
from utils            import verbosity, items_to_dict


class Words(dict):
    url = "http://www.portaldalinguaportuguesa.org/?action=novoacordo&act=list&letter=%s&version=pe"
     
    def __init__(self, dic):
        self.update( dic )
        self.original = dic.items()
        

    @classmethod
    def get(self, char):
        find       = lambda regex, string, sep: re.findall( regex, string )[0].split( sep )
        find_words = lambda regex, table: [ find( regex, row, ',' )[0] for row in table if row ]
        response = requests.get( self.url%char ).content.replace( '\n', '' )    
        table    = find( WORDS_REGEX, response, '<tr' )
        words    = zip( find_words(DAO_REGEX, table), find_words(AAO_REGEX, table) )
        return self( items_to_dict(words) )


    def add_variants(self):
        self.add_feminines()
        self.add_plurals()
        self.add_conjugations()
        self.remove_redundancy()

        
    def with_variants(self):
        self.add_variants()
        return self


    @verbosity('> adding plural form')
    def add_plurals(self):
        for dao,aao in self.items():
            try:
                if dao and aao:
                    self[ Grammar.DAO.get_plural(dao) ] = Grammar.AAO.get_plural(aao)
            except NoInputGiven:
                continue


    @verbosity('> adding feminine form')
    def add_feminines(self):
        for dao,aao in self.items():
            try:
                if dao and aao:
                    self[ Grammar.DAO.get_feminine(dao) ] = Grammar.AAO.get_feminine(aao)
            except NoInputGiven:
                continue


    @verbosity('> adding verb conjugations')
    def add_conjugations(self):
        def conjugations(d,a):
            dao_ = Grammar.DAO.get_conjugations(d)
            aao_ = Grammar.AAO.get_conjugations(a)
            if dao_ and aao_:
                if len(dao_)==len(aao_):
                    return zip(dao_, aao_)
                if Settings.VERBOSE:
                    print "\nWARNING: could not conjugate '%s' and '%s' properly." %(d,a)
            return []

        words = [conjugations(dao, aao) for dao,aao in self.original if dao and aao]
        self.update( dict( reduce(lambda a,b: a+b, words) ) )                


    @verbosity('> removing redundancy')
    def remove_redundancy(self):
        for dao,aao in self.items():
            if dao==aao or not dao or not aao:
                self.pop( dao )

