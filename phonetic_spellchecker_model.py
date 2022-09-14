from spellchecker import SpellChecker
from difflib import SequenceMatcher
import json
import pickle
import math   

class SpellCheckPhone:

    def __init__(self, dict_path, char_mistake_path, letter_prob_path) -> None:
        # Initiating the hebrew dictionary
        self.spell = SpellChecker(
            language=None, case_sensitive=True, distance=2)
        self.spell.word_frequency.load_dictionary(dict_path)
        self.letter_description_after_scoring = self.letters_scores_building(
            char_mistake_path, letter_prob_path)

    # Pickle functions
    @staticmethod
    def get_letters_pickle(address):
        """
        Returns the letters dictionary.
        Arguments:
            address(String) - The address of the pickle. 
        Returns:
            Dictionary. The dictionary of the letters. 
        """
        with open(address, "rb") as f:
            pickle_out = pickle.load(f)
        return pickle_out

    # Json and Dictionary Functions

    @staticmethod
    def parse_letter_dictionary(letters_dictionary):
        """
        Parsing the replaces key in the dictionary to list of tuples.
        Arguments:
            letters_dictionary(Dictionary) - the letters dictionary.
        Returns:
            List(tuples) - the list of replaces tuples.
        """
        letters_switches = []  # List of tuples
        for key, value in letters_dictionary['replaces'].items():
            letters_switches_tuple = (key[0], key[1])
            letters_full_switches_tuple = (letters_switches_tuple, value)
            letters_switches.append(letters_full_switches_tuple)
        return letters_switches

    # Reading json file

    @staticmethod
    def json_loads_file(file):
        """Get file json.loads .

        Args:
            file(string): path to the json file.

        Returns:
            file. json file.
        """
        with open(file, encoding="utf8", mode='r') as f:
            data = json.load(f)
            return data

    @staticmethod
    def list_of_jsons_to_letters_dictionary(list_of_jsons):
        """
        Converting List of jsons to only one dictionary with the letters as key and the probabilities as value.
        Arguments:
            list_of_jsons(List) - The list of jsons described each letter
        Returns:
            Dictionary. The dictionary holds all characters
        """
        myDict = {}
        my_subDict = {'subs': 0, 'add': 0, 'replace': {}}
        for letter in list_of_jsons:
            my_subDict['subs'] = letter['subs']
            my_subDict['add'] = letter['add']
            my_subDict['replace'] = letter['replace']
            myDict[letter['letter']] = my_subDict
            my_subDict = {'subs': 0, 'add': 0, 'replace': {}}
        return myDict

    @staticmethod
    def get_final_candidate(candidates_scores):
        """
        Finds the key with the minimal value.
        Arguments:
            candidates_scores(Dictionary) - the candidates dictionary.
        Returns:
            String. the candidate word.        
        """
        return(min(candidates_scores, key=candidates_scores.get))

    @staticmethod
    def sort_dict_by_minimum(candidates_scores):
        """
        Sorts the dictionary by its minimum values.
        Arguments:
            my_dict(Dictionary)
        """
        candidates_scores_keys_sorted = sorted(candidates_scores.keys())
        candidates_scores_values_sorted = sorted(candidates_scores.values())
        candidates_sorted = {}
        for i in range(len(candidates_scores_keys_sorted)):
            candidates_sorted[candidates_scores_keys_sorted[i]
                              ] = candidates_scores_values_sorted[i]
        # print(candidates_sorted)

    # Building the letters dictionary scores

    def switches_confusion_matrix_scoring(self, letters_description, common_switches):
        """
        Scoring the letters switches based on the confusion matrix .
        Arguments:
            letters_description(Dictionary) - letters probabilities.
            common_switches(List) - switches probabilities.
        Returns:
            Dictionary. The letters_description probabilities. 
        """
        # put the information from the confusion matrix(described by the variable common_switches) into the letters_description
        for letters_pair in common_switches:
            letters_description[letters_pair[0][0]
                                ]['replace'][letters_pair[0][1]] = letters_pair[1]

        # running on every key in the dictionary
        for origin_letter in letters_description:
            for model_letter, score in letters_description[origin_letter]['replace'].items():
                if score > 0 and score < 1:
                    letters_description[origin_letter]['replace'][model_letter] = 0
        return letters_description

    def insertion_and_remove_commonly_score(self, letters_description_dictionary, letters_dictionary):
        """
        Puts the scores of insertion and remove in each letter.
        Arguments: 
            letters_description_dictionary(dictionary) - letters scores.
            letters_dictionary(dictionary) - the full scores of the letters to each operation.
        Returns:
            dictionary. The dictionary describes the common scores of substitution, insertion and remove.
        """
        for letter in letters_dictionary['inserts'].keys():
            letters_description_dictionary[letter]['add'] = letters_dictionary['inserts'][letter]
        for letter in letters_dictionary['deletes'].keys():
            letters_description_dictionary[letter]['subs'] = letters_dictionary['deletes'][letter]
        return letters_description_dictionary

    def find_max_score(self, letters_description):
        """
        Finds the max score in a letters dictionary
        Arguments:
            letters_description(dictionary) -Letters dictionary.
        Returns:
            int. the maximum number
        """
        maximum_score = 0
        for letter in letters_description.keys():
            if letters_description[letter]['subs'] > maximum_score:
                maximum_score = letters_description[letter]['subs']
            if letters_description[letter]['add'] > maximum_score:
                maximum_score = letters_description[letter]['add']
            for switch_score in letters_description[letter]['replace'].values():
                if switch_score > maximum_score:
                    maximum_score = switch_score
        return maximum_score

    def letters_calculation_scores(self, letters_description, max_score):
        """
        Calculates the scoring inversly to the term frequency using equation.
        Arguments:
            letters_description(Dictionary) - the dictionary contains the whole probabilities
            max_score(int) - the maximmum value in the dictionary
        Returns:

        """
        for original_letter in letters_description:
            for model_letter, score in letters_description[original_letter]['replace'].items():
                letters_description[original_letter]['replace'][model_letter] = (math.log(max_score - score + 2 ,11))/ (max_score)
            letters_description[original_letter]['subs']= (math.log(max_score - letters_description[original_letter]['subs'] +2 ,11))/ max_score
            letters_description[original_letter]['add'] =  (math.log(max_score - letters_description[original_letter]['add'] +2 ,11))/ max_score
        return letters_description
        # for original_letter in letters_description:
        #     for model_letter, score in letters_description[original_letter]['replace'].items():
        #         letters_description[original_letter]['replace'][model_letter] = (
        #             max_score - score + 2) / (max_score)
        #     letters_description[original_letter]['subs'] = (
        #         max_score - letters_description[original_letter]['subs'] + 2) / max_score
        #     letters_description[original_letter]['add'] = (
        #         max_score - letters_description[original_letter]['add'] + 2) / max_score
        # return letters_description

    def compare_letters_scoring(self, letter_description_after_scoring):
        """
        Updates  the score of substitution if the score of insertion and remove smaller than the subtitution.
        Arguments:
            letter_description_after_scoring(dictionary) - the score of the letters different cases.
        Returns:
            Dictionary. The updated score of the letters 
        """
        for original_letter in letter_description_after_scoring.keys():
            for model_letter in letter_description_after_scoring[original_letter]['replace'].keys():
                if letter_description_after_scoring[original_letter]['replace'][model_letter] > letter_description_after_scoring[original_letter]['subs'] + letter_description_after_scoring[model_letter]['add']:
                    letter_description_after_scoring[original_letter]['replace'][model_letter] = letter_description_after_scoring[
                        original_letter]['subs'] + letter_description_after_scoring[model_letter]['add']
        return letter_description_after_scoring     

    # Filter candidates functions

    def filter_candidates(self, candidates):
        """
        #     Finds the words we should remove from the candidates list.
        #     Arguments:
        #         candidates(List) - the candidates list.
        #     Returns:
        #         List. The words we should remove from the candidates list.
        #     """

        words_to_remove = []
        for candidate in candidates:
            if candidate[-1] in 'מנפצכ':
                words_to_remove.append(candidate)
                continue
            elif candidate.count('"') > 1:
                words_to_remove.append(candidate)
                continue
            else:
                for candidate_letter in candidate:
                    if candidate_letter in 'ןםךץף':
                        if candidate.find(candidate_letter) != (len(candidate)-1):
                            words_to_remove.append(candidate)
                            break
                    elif candidate_letter in '"':
                        if candidate.find(candidate_letter) != (len(candidate)-2):
                            words_to_remove.append(candidate)
                            break
        return words_to_remove

    def remove_words_from_list(self, original_list, words_to_remove):
        """
        Removing each word from words_to_remove from the original_list.
        Arguments:
            original_list(List) - the original list.
            words_to_remove(List) - the list that contains the words we should remove.
        Returns:
            List. The list after the words filtering.
        """
        for remove_word in words_to_remove:
            original_list.remove(remove_word)
        return original_list

    def remove_duplicates_from_list(self, my_list):
        """
        Removes the duplicates elements from a list.
        Arguments:
            my_list(List) - the original list.
        Returns:
            List. The list without the duplicates.
        """
        my_list = list(dict.fromkeys(my_list))
        return my_list

    # Converting suffix function

    def converting_suffix(self, candidate):
        """
        Convert back the final letter from regular letter to suffix letter.
        Arguments:
            candidate(String) - the candidate word
        Returns:
            String - the candidate with suffix.
        """
        suffix_map = str.maketrans("מנצפכ", "םןץףך")
        if candidate[-1] in 'כמנצפ':
            candidate = candidate[:-1] + candidate[-1].translate(suffix_map)
        return candidate

    # Candidates scoring functions

    # Omission and insertion scores

    def letter_omission_score(self, letter_description_after_scoring, candidate_letter):
        """
        Calculates the the score of candidate letter omission.
        Arguments:
            letter_description_after_scoring(dictionary) - the score of the letters different cases.
            candidate_letter(char) - the letter we should consider its score to omit.
        Returns:
            Double. The score of the letter ommision.
        """
        return letter_description_after_scoring[candidate_letter]['subs']

    def letter_addition_score(self, letter_description_after_scoring, model_letter):
        """
        Calculates the the score of missplled word letter insertion.
        Arguments:
            letter_description_after_scoring(dictionary) - the score of the letters different cases.
            model_letter(char) - the letter we should consider its score to insert.
        Returns:
            Double. The score of the letter insertion.
        """
        return letter_description_after_scoring[model_letter]['add']

    # Replacement scores functions

    # Letter vs letter

    # model letter vs candidate letters

    def candidate_letters_by_model_letter(self, letter_description_after_scoring, model_letter, candidate_letters):
        """
         Finds the minimum score between two candidate letters replacement by one model letter.
         Arguments:
             letter_description_after_scoring(dictionary) - the score of the letters different cases.
             model_letter(String) - letter of the model.
             candidate_letters(String) - letters of the candiate.
         Returns:
             Double. The minimum score of the letter replacement/omission/insertion.
         """
        sequence_score = 0
        if (letter_description_after_scoring[candidate_letters[0]]['replace'][model_letter] + letter_description_after_scoring[candidate_letters[1]]['subs']) <= (letter_description_after_scoring[candidate_letters[1]]['replace'][model_letter] + letter_description_after_scoring[candidate_letters[0]]['subs']):
            sequence_score = letter_description_after_scoring[candidate_letters[0]]['replace'][
                model_letter] + letter_description_after_scoring[candidate_letters[1]]['subs']
        else:
            sequence_score = letter_description_after_scoring[candidate_letters[1]]['replace'][
                model_letter] + letter_description_after_scoring[candidate_letters[0]]['subs']
        return sequence_score

    def candidate_letter_by_model_letters(self, letter_description_after_scoring, model_letters, candidate_letter):
        """
        Finds the minimum score between two candidate letters replacement by one model letter.
        Arguments:
            letter_description_after_scoring(dictionary) - the score of the letters different cases.
            model_letters(String) - letters of the model.
            candidate_letter(String) - letter of the candiate.
        Returns:
            Double. The minimum score of the letter replacement/omission/insertion.
        """
        sequence_score = 0
        if (letter_description_after_scoring[candidate_letter]['replace'][model_letters[0]] + letter_description_after_scoring[model_letters[1]]['add']) <= (letter_description_after_scoring[candidate_letter]['replace'][model_letters[1]] + letter_description_after_scoring[model_letters[0]]['add']):
            sequence_score = letter_description_after_scoring[candidate_letter]['replace'][
                model_letters[0]] + letter_description_after_scoring[model_letters[1]]['add']
        else:
            sequence_score = letter_description_after_scoring[candidate_letter]['replace'][
                model_letters[1]] + letter_description_after_scoring[model_letters[0]]['add']
        return sequence_score

    def candidate_letters_by_model_letters(self, letter_description_after_scoring, model_letters, candidate_letters):
        """
        Calculates the letters by letters replecment.
        Arguments:
            letter_description_after_scoring(dictionary) - the score of the letters different cases.
            model_letters(String) - the letters of the model we should consider its score to replace.
            candidate_letters(String) - the letters of the candidate we should consider its score to replace.
        Returns:
            Double. The score of the letter replacement. 
        """
        candidate_score = 0
        if (letter_description_after_scoring[candidate_letters[0]]['replace'][model_letters[0]] + letter_description_after_scoring[candidate_letters[1]]['replace'][model_letters[1]] < letter_description_after_scoring[candidate_letters[0]]['replace'][model_letters[1]] + letter_description_after_scoring[candidate_letters[1]]['subs'] + letter_description_after_scoring[candidate_letters[0]]['add']):
            candidate_score = letter_description_after_scoring[candidate_letters[0]]['replace'][model_letters[0]
                                                                                                ] + letter_description_after_scoring[candidate_letters[1]]['replace'][model_letters[1]]
        else:
            candidate_score = letter_description_after_scoring[candidate_letters[0]]['replace'][model_letters[1]] + \
                letter_description_after_scoring[candidate_letters[1]]['subs'] + \
                letter_description_after_scoring[candidate_letters[0]]['add']
        return candidate_score

    def letters_replacement_score(self, letter_description_after_scoring, model_letters, candidate_letters):
        """
        Calculates the replacement score.
        Arguments:
            letter_description_after_scoring(dictionary) - the score of the letters different cases.
            model_letters(String) - the letters of the model we should consider its score to replace.
            candidate_letters(String) - the leters of the candidate we should consider its score to replace.
        Returns:
            Double. The score of the letter replacement.
        """
        candidate_score = 0
        if len(model_letters) == 1 and len(candidate_letters) == 1:
            candidate_score += letter_description_after_scoring[candidate_letters]['replace'][model_letters]
        elif len(model_letters) == 1 and len(candidate_letters) > 1:
            candidate_score += self.candidate_letters_by_model_letter(
                letter_description_after_scoring, model_letters, candidate_letters)
        elif len(model_letters) > 1 and len(candidate_letters) == 1:
            candidate_score += self.candidate_letter_by_model_letters(
                letter_description_after_scoring, model_letters, candidate_letters)
        elif len(model_letters) > 1 and len(candidate_letters) > 1:
            candidate_score += self.candidate_letters_by_model_letters(
                letter_description_after_scoring, model_letters, candidate_letters)
        return candidate_score

    def sort_candidates(self, model_word, candidates, letter_description_after_scoring):
        """
        Sorts the missplled word candidates by scoring.
        Arguments:
            model_word(str) - The missplled word
            candidates(List) - The correction candidates
            letter_description_after_scoring(dictionary) - the probability of the letters.
        Returns:
            Dictionary. The scores dictionary.
        """
        candidates_scores = {}
        candidate_score = 0
        for candidate in candidates:
            # print('\n')
            suffix_map = str.maketrans("םןץףך", "מנצפכ", '"')
            candidate = candidate.translate(suffix_map)
            model_word = model_word.translate(suffix_map)
            d = SequenceMatcher(None, model_word, candidate)
            for tag, i1, i2, j1, j2 in d.get_opcodes():
                # print('{:7}   model_word[{}:{}] --> candidate[{}:{}] {!r:>8} --> {!r}'.format(
                #     tag, i1, i2, j1, j2, model_word[i1:i2], candidate[j1:j2]))
                if tag == 'insert':
                    for candidate_letter in candidate[j1:j2]:
                        candidate_score += self.letter_omission_score(
                            letter_description_after_scoring, candidate_letter)
                elif tag == 'delete':
                    for model_letter in model_word[i1:i2]:
                        candidate_score += self.letter_addition_score(
                            letter_description_after_scoring, model_letter)
                elif tag == 'replace':
                    candidate_score += self.letters_replacement_score(
                        letter_description_after_scoring, model_word[i1:i2], candidate[j1:j2])
            candidate = self.converting_suffix(candidate)
            candidates_scores[candidate] = candidate_score
            #print(f'The candidate total score is: {candidate_score}')
            candidate_score = 0
            # print('\n')
        return candidates_scores

    # filtering scores

    def filter_scores(self, candidates_scores):
        """
        Removes the words with score 0.
        Arguments:
            candidates_scores(Dictionary) - Words with their score.
        Returns:
            Dictionary. The filtered dictionary.
        """
        candidates_final_scores = {}
        for key, value in candidates_scores.items():
            if value != 0:
                candidates_final_scores[key] = value
        return candidates_final_scores

    def letters_scores_building(self, char_mistake_path, letter_prob_path):
        # Letters switches list based on Dina's confusion matrix
        letters_dictionary = self.get_letters_pickle(char_mistake_path)
        # "((supposed to be,model's output),number describe the frequency of substitution)"
        letters_switches = self.parse_letter_dictionary(letters_dictionary)
        # The letter description - List of dictionaries(each dictionary is a letter with all the probabilities)
        letters_description = self.json_loads_file(letter_prob_path)
        # Parsing the List of dictionaries to one dictionary when the letters are the only keys
        letters_description_dictionary = self.list_of_jsons_to_letters_dictionary(
            letters_description)
        # Insert the scores from the letters switches list of tuples(based on the confusion matrix)
        letters_description = self.switches_confusion_matrix_scoring(
            letters_description_dictionary, letters_switches)
        letters_description = self.insertion_and_remove_commonly_score(
            letters_description, letters_dictionary)
        maximum_score = self.find_max_score(letters_description)
        # Getting the different scores to each letter - score of substitution, insertion and remove
        letter_description_after_scoring = self.letters_calculation_scores(
            letters_description, maximum_score)
        letter_description_after_scoring = self.compare_letters_scoring(
            letter_description_after_scoring)
        return letter_description_after_scoring

    def get_candidate(self, word):
        """
        Finds the candidate of a word based on phonetic similarity.
        Arguments:
            word(String) - the word we check
        Returns:
            String. The candidate word.
        """

        # Getting a list of misspelled word
        misspelled = self.spell.unknown([word])
        if misspelled:
            for word in misspelled:
                # finds the candidates at first
                # lev_dist1 = list(self.spell.edit_distance_1(word))
                # lev_dist2 = list(self.spell.edit_distance_2(word))
                # total_candidates = lev_dist1 + lev_dist2

                res1 = [x for x in self.spell.edit_distance_1(word)]
                res2 = [x for x in self.spell.edit_distance_2(word)]
                tmp1 = self.spell.known(res1)
                tmp2 = self.spell.known(res2)
                total_candidates = list(tmp1.union(tmp2))
                # filtering the words - removing the unlogical words
                words_to_remove = self.filter_candidates(total_candidates)
                total_candidates = [
                    x for x in total_candidates if x not in words_to_remove+[word]]
#                 total_candidates = self.remove_words_from_list(
#                     total_candidates, words_to_remove)

#                 # removing the duplicates words
#                 total_candidates = self.remove_duplicates_from_list(total_candidates)

#                 # removing the mistaken word itself from the candidates
#                 total_candidates.remove(word)

                # letter_description_after_scoring = self.letters_scores_building()

                # finds the scores of each candidate
                candidates_scores = self.sort_candidates(
                    word, total_candidates, self.letter_description_after_scoring)
                candidates_scores = self.filter_scores(candidates_scores)
                # sort_dict_by_minimum(candidates_scores)
                candidate = self.get_final_candidate(candidates_scores)
        else:
            candidate = word
        return candidate
