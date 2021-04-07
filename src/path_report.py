import logging
from fuzzywuzzy import fuzz
from src.constants import special_char_replacement, text_numbers, extra_info
logger = logging.getLogger("PATH_REPORT_LOGGER")
HEADING = 'Heading'
REGION = 'Region'
EXTRA = 'Extra_Info'
ATTRIBUTES = ['Pos_Cores','Total_Cores','Gleason_Primary','Gleason_Secondary','Gleason_Total','Cancer_Dx']
BEGIN = 'B'
INNER = 'I'
Outter = 'O'
Data_Dir = "Data/NLP/PreProcessed/scispacy/"

class PathologyReport:

    def __init__(self, filename, vector_reps, data_dir=Data_Dir, raw_text=None):
        self.filename = filename
        self.vecs = vector_reps
        self.num_sents = len(self.vecs)
        self.predictions = None
        self.SECTIONS = {'START':[]}    # keeps track of every non-O tag found in a section
        self.REGIONS = {'START':{}}     # keeps track of ATTRIBUTE-REGION links per section
        self.FLOATING = {'START':{}}    # tags that have no region
        self.EXTRA = []
        self.LABEL_DICT = {}
        if filename:
            self.fulltext = open(data_dir + filename,'r').read()
        else:
            self.fulltext = raw_text
        self.resolved_regions = None
        self.grade = None
        self.extra_info_counts = None
        self.gleason_score = None


    def add_region(self,section,region_name):
        self.REGIONS[section].setdefault(region_name, {})
        for attribute in ATTRIBUTES:
            self.REGIONS[section][region_name].setdefault(attribute,[])
        return True

    def get_text(self,bounds_list,line):
        return self.fulltext[bounds_list[0][0]:bounds_list[-1][1]]

    def get_tag_info(self,tag):
        type = tag.split('-')[1] if tag != Outter else Outter
        is_begin = BEGIN in tag
        is_inner = INNER in tag
        return type, is_begin, is_inner

    def extract_tag(self, current_bounds_list, line,prev_tag_type, curr_section):
        new_section = False
        text = self.get_text(current_bounds_list, line).strip()
        # record this text in tag dictionary
        self.LABEL_DICT.setdefault(prev_tag_type, [])
        self.LABEL_DICT[prev_tag_type].append(text)

        if prev_tag_type == HEADING:
            self.SECTIONS.setdefault(text, [])  # add a new section
            curr_section = text
            new_section = True
        else:
            if prev_tag_type != Outter:
                self.SECTIONS[curr_section].append((prev_tag_type, text))
        return text, new_section

    def realize_predictions(self):
        curr_section = 'START'
        prev_b = False
        prev_i = False
        prev_tag_type = None
        current_bounds_list = []
        global_offset = 0
        for pred_id, prediction_vector in enumerate(self.predictions):
            for i, current_tag in enumerate(prediction_vector):
                current_tag_type, is_begin, is_inner = self.get_tag_info(current_tag)
                if not prev_tag_type:
                    prev_tag_type = current_tag_type
                    prev_b = is_begin
                    prev_i = is_inner

                else:
                    if not (prev_tag_type == current_tag_type) or is_begin:
                        # we need to extract the text for this tag and add it to section array
                        l = self.vecs[pred_id]['RAW']
                        text, new_sect = self.extract_tag(current_bounds_list,self.vecs[pred_id]['RAW'],prev_tag_type,curr_section)
                        if new_sect:
                            curr_section = text
                        current_bounds_list = []

                current_bounds_list.append(self.vecs[pred_id]['TOKEN_BOUNDS'][i])
                prev_tag_type = current_tag_type
                prev_b = is_begin
                prev_i = is_inner

            text, new_sect = self.extract_tag(current_bounds_list, self.vecs[pred_id]['RAW'], prev_tag_type, curr_section) # handle final tokens in line
            if new_sect:
                curr_section = text
            current_bounds_list = []
            prev_b = False
            prev_i = False
            prev_tag_type = None

        return None

    def populate_regions(self):
        for section in self.SECTIONS:
            self.FLOATING.setdefault(section,{})
            self.REGIONS.setdefault(section,{})
            current_region = None
            for tupl in self.SECTIONS[section]:
                tag = tupl[0]
                text = tupl[1]
                if tag == REGION:
                    current_region = text
                    self.add_region(section,current_region)
                elif tag in ATTRIBUTES:
                    if current_region:
                        """
                        if self.REGIONS[section][region_id][tag]:
                            logger.warning("In file {}, overwriting attribute {}, later tag found...\n\t{}\t->\t{}".format(
                                self.filename,tag,self.REGIONS[section][region_id][tag],text
                            ))
                        """
                        if not self.REGIONS[section][current_region][tag]:   # only allow one of each attribute per region PER section
                            self.REGIONS[section][current_region][tag].append(text)
                    else:
                        # have a region attribute with no prior region labeled, put in floating
                        self.FLOATING[section].setdefault(tag,[])
                        self.FLOATING[section][tag].append(text)
                elif tag == EXTRA:
                    self.EXTRA.append(text)
                    continue
            # Move onto the next section


        return None

    def get_region_similarity(self,string1,string2):
        return fuzz.token_sort_ratio(string1,string2)

    def match_region_set(self,agreggated_set,new_set):
        # we'll need a matrix of scores
        scores = {}
        for r1 in agreggated_set:
            for r2 in new_set:
                scores[(r1,r2)] = self.get_region_similarity(r1,r2)
        debug = True

        sorted_scores = sorted([tupl for tupl in scores.items()],key=lambda x:x[1],reverse=True) # form: [ ( (aggregate_region, new_regoin), score ) , ...]
        # match each region from the new set to the aggregated set.
        choices = {}
        average_score = sum(list(scores.values()))/len(scores)
        for score in sorted_scores:
            r1, r2, sim = score[0][0], score[0][1], score[1]

            if r1 not in choices and r2 not in choices.values() and sim > average_score: # if we haven't mapped this region yet AND its similarity is greater than half of the average similarity, match
                choices[r1] = r2

        # now we need to figure out the unatched regions, we'll be treating these as new
        new_regions = [r for r in new_set if r not in list(choices.values()) + list(choices.keys())]

        return choices, new_regions

    def region_resolution(self):
        # aggregate all matching region information across sections
        aggregated_regions = {}
        # Do we find regions in different sections? If so, are there a different number of regions?
        for section in self.REGIONS:
            if not self.REGIONS[section]:
                # if no regions in this section, skip
                do_nothing = True
            else:
                if not aggregated_regions:
                    # if we haven't added any regions to our aggregated regions map, then just use the current section's regions
                    aggregated_regions = self.REGIONS[section]
                    debug = True
                else:
                    # we also have regions in this section, we need to find the best match for each region
                    current_regions = self.REGIONS[section]
                    choices, new_regions = self.match_region_set(aggregated_regions,current_regions)
                    debug = True

                    # combine all attributes of matched regions in aggregated regions
                    for r1, r2 in choices.items():
                        for attribute in current_regions[r2]:
                            for val in current_regions[r2][attribute]:
                                aggregated_regions[r1][attribute].append(val)
                    #  lastly, add new regions to aggregate if any were found

                    for region in new_regions:
                        aggregated_regions[region] = current_regions[region]
        self.resolved_regions = aggregated_regions
        return None

    def resolve_gleason_score(self,item):
        # the gleason score we tagged isn't only an integer figure it out here
        if item.isdigit():
            num = int(item)
            if num > 10:
                return int(item[0]) # just return the first digit, its most likely a double number or misread equation
            else:
                return num
        lower = item.lower()
        if lower in text_numbers:
            return text_numbers[lower]
        elif lower in special_char_replacement:
            return special_char_replacement[lower]
        debug = True
        return 0

    def resolve_core_classification(self, items):
        resolved = []
        for item in items:
            if item.isdigit():
                resolved.append(int(item))
            lower = item.lower()
            if lower in text_numbers:
                resolved.append(text_numbers[lower])
            if lower in special_char_replacement:
                resolved.append(special_char_replacement[lower])

        return resolved


    def calculate_grade(self,primary, secondary, total, simple=True):
        """
        Simple stratification is from the PCPR, not most recent prostate cancer schema
        """
        if simple:
            if total <= 6:
                return 1
            elif total > 7:
                return 3
            else:
                return 2
        if total == 0:
            if primary + secondary == 0:
                return 0
            else:
                total = primary + secondary

        # calculate grade
        if total <= 6:
            return 1
        elif total == 7:
            if primary == 3 and secondary == 4:
                return 2
            elif primary == 4 and secondary == 3:
                return 3
            else:
                # return worst case
                debug = True
                return 3
        elif total == 8:
            return 4
        elif total >= 9:
            return 5
        return None

    def count_extra_info(self):
        counts = {k:0 for k in extra_info}
        for info in self.EXTRA: # for every string we flagged as extra info
            categorized = False
            for category in extra_info:
                keywords = extra_info[category][0:-1]
                token_distance_words = extra_info[category][-1].split('|||')
                if any([keyword in info for keyword in keywords]) or any([fuzz.token_sort_ratio(info,w) > 50 for w in token_distance_words]):
                    counts[category] +=1
        return counts

    def _max_candidate(self,candidates):
        full_support_candidates = [c for c in candidates if c[1] == 3]
        two_support_candidates = [c for c in candidates if c[1] == 2]
        total_only_candidates = [c for c in candidates if c[1] == 1]

        # in order of support priority, sort by highest total and then highest primary
        if full_support_candidates:
            return sorted(full_support_candidates, key=lambda x: (x[0][0],x[0][2]), reverse=True)[
                0]  # get candidate with highest primary gleason)
        elif two_support_candidates:
            return sorted(two_support_candidates, key=lambda x: (x[0][0],x[0][2]), reverse=True)[0]
        elif total_only_candidates:
            return sorted(total_only_candidates, key=lambda x: (x[0][0],x[0][2]), reverse=True)[0]
        return None

    def find_best_region_candidate(self,primaries,secondaries,totals):
        candidates = []
        total_cands = [t for t in totals if t <=10]
        for total in total_cands:
            # for each gleason_total we have, check if we have support primary and secondary vals
            sums = []
            if not primaries:
                if not secondaries:
                    candidates.append((   (total - 1, 1,total)  ,   1 )  ) # TODO worst case score is 5 for prim or secondary, but this is low support

                for s in secondaries:
                    candidates.append((   (total - s, s ,total)  ,   2 ) )
            elif not secondaries:
                for s in primaries:
                    candidates.append(((s, total - s, total), 2))
            else:
                # we have both primary and secondary vals
                sums = [(p, s) for p in primaries for s in secondaries]
                max_pair = ((-1000,None,None),-1000)
                for pair in sums:
                    if pair[0] + pair[1] == total:
                        if pair[0] > max_pair[0][0]:
                            max_pair = (   (pair[0],pair[1],total), 3  )
                    else:
                        if pair[0] > max_pair[0][0]:
                            max_pair = (   (pair[0],pair[1],pair[0] + pair[1]), 2  ) # 2 support because didn't add up to total
                if max_pair[0][2]:
                    candidates.append(max_pair)
        if not candidates and (primaries and secondaries):
            sums = [(p, s) for p in primaries for s in secondaries]
            max_pair = ((-1000, None, -1000), -1000)
            for pair in sums:
                    if pair[0] > max_pair[0][0] and pair[0] + pair[1] > max_pair[0][2]: # if the primary of this is highest so far and has a bigger total...
                        max_pair = (
                        (pair[0], pair[1], pair[0] + pair[1]), 2)  # 2 support because didn't have total
            if max_pair[0][2]:
                candidates.append(max_pair)
            return self._max_candidate([c for c in candidates if c[0][2] <=10])
        else:
            return self._max_candidate([c for c in candidates if c[0][2] <=10])
        return None

    def extract_gleason_from_section(self,section_tags):
        primaries, secondaries, totals = [], [] , []
        debug = True
        if 'Gleason_Primary' in section_tags:
            primaries.extend([self.resolve_gleason_score(score) for score in section_tags['Gleason_Primary']])
        if 'Gleason_Secondary' in section_tags:
            secondaries.extend([self.resolve_gleason_score(score) for score in section_tags['Gleason_Secondary']])
        if 'Gleason_Total' in section_tags:
            totals.extend([self.resolve_gleason_score(score) for score in section_tags['Gleason_Total']])
        if primaries.__len__() >=8 and secondaries.__len__() >=8 and totals.__len__() >= 8: # this is probably a WHO section
            return [], [] ,[]
        return primaries, secondaries ,totals

    def extract_gleason(self):
        gleason_scores = [
            [self.resolved_regions[r]['Gleason_Primary'],
             self.resolved_regions[r]['Gleason_Secondary'],
             self.resolved_regions[r]['Gleason_Total']

             ] for r in self.resolved_regions]

        for i, triple in enumerate(gleason_scores):
            for j, score_arr in enumerate(triple):
                for k, score in enumerate(score_arr):
                    x = gleason_scores[i][j][k] = self.resolve_gleason_score(score)

        candidates = []

        for i, region in enumerate(gleason_scores):
            totals = []
            primaries = []
            secondaries = []

            if region[0]:
                primaries.extend(region[0])
            if region[1]:
                secondaries.extend(region[1])
            if region[2]:
                totals.extend(region[2])
            totals = [x for x in totals if x != 0]
            primaries = [x for x in primaries if x != 0]
            secondaries = [x for x in secondaries if x != 0]

            best_candidate = self.find_best_region_candidate(primaries, secondaries, totals)
            if best_candidate:
                candidates.append(best_candidate)

        max_candidate = self._max_candidate(candidates)

        debug = True

        """
        If we didn't get a candidate from above, lets check the floating sections
        """

        if not max_candidate:
            floating_primaries, floating_secondaries, floating_totals = [], [], []
            for section in self.FLOATING:
                p, s, t = self.extract_gleason_from_section(self.FLOATING[section])
                floating_primaries.extend(p)
                floating_secondaries.extend(s)
                floating_totals.extend(t)
            max_candidate = self.find_best_region_candidate(floating_primaries, floating_secondaries, floating_totals)

        primary = max_candidate[0][0] if max_candidate else 0
        secondary = max_candidate[0][1] if max_candidate else 0
        total = max_candidate[0][2] if max_candidate else 0
        return primary, secondary, total


    def is_malignant(self,info):
        """
        If don't have positive cores, but have evidence of malignancy, we'll want to know
        """
        if any([info['Gleason_Primary'],
                info['Gleason_Secondary'],
                info['Gleason_Total'],
                info['Cancer_Dx']
                ]):
            return True
        return False

    def extract_cores(self):
        # 4-tuples of (region name, [pos cores], [total cores], malignancy)
        regions = [ (r,self.resolve_core_classification(self.resolved_regions[r]['Pos_Cores']),
                     self.resolve_core_classification(self.resolved_regions[r]['Total_Cores']),
                    self.is_malignant(self.resolved_regions[r]))
                    for r in self.resolved_regions]

        pos, total = 0, 0
        for region, pos_cores, total_cores, status in regions:
            _pos, _total = None, None
            if total_cores:
                _total = max(total_cores)
            else:
                _total = 1
            if pos_cores:
                _pos = max(pos_cores)
            else:
                if status:
                    _pos = _total #TODO assume all cores are malignant if no positive given?
                else:
                    _pos =  0
            pos   +=  _pos
            total +=  _total
        debug = True
        return pos, total

    def stratify(self):

        # Extract relevent gleason scores
        primary, secondary, total = self.extract_gleason()
        self.gleason_score = [primary, secondary, total]
        self.grade = self.calculate_grade(primary, secondary, total)

        # get pos cores / total cores
        self.pos_cores, self.total_cores = self.extract_cores()

        # get extra info
        self.extra_info_counts = self.count_extra_info()
        return None


