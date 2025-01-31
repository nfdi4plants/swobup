import obonet
import datetime

from app.helpers.models.ontology.term import Term
from app.helpers.models.ontology.ontology import Ontology
from app.helpers.models.ontology.relationships import Relationships
from app.helpers.models.ontology.obo_file import OboFile

from app.helpers.notifications.models.notification_model import Notifications, Message


class OBO_Parser:
    def __init__(self, ontology_file):
        self.ontology_file = ontology_file
        self.nodes = []
        self.relations = []

        self.metadata = []

        self.ontolgies = []

        self.relationships = []

        self.obo_file = OboFile()

        self.collected_terms = set()
        self.collected_ontologies = set()

        self.typedefs = {}

    def get_author_list(line):
        # Cleans author dataframe column, creating a list of authors in the row.
        return [e[1] + ' ' + e[0] for e in line]

    def get_category_list(line):
        # Cleans category dataframe column, creating a list of categories in the row.
        return list(line.split(" "))

    def get_ontology_list(self):
        return self.ontolgies

    def get_relations(self):
        return self.relationships

    # def ontology_available(self, node_prefix):
    #     for ontology in self.obo_file.ontologies:
    #         if node_prefix == ontology.name:
    #             return True
    #     return False

    def ontology_available(self, node_prefix):
        if node_prefix in self.collected_ontologies:
            return True
        return False

    # def term_available(self, term_accession):
    #     for term in self.obo_file.terms:
    #         if term_accession == term.accession:
    #             return True
    #     return False

    # def term_available(self, term_accession):
    #     if term_accession in self.collected_terms:
    #         return True
    #     return False

    def term_available(self, term_accession):
        if term_accession in self.collected_terms:
            return True
        return False

    # def term_available(self, term_accession):
    #     if term_accession in self.obo_file.terms:
    #         return True
    #     return False

    def get_ontology_name(self):
        ontology_name = None
        try:
            graph = obonet.read_obo(self.ontology_file, ignore_obsolete=False)
            ontology_name = graph.graph.get("name", None)
            ontology_author = graph.graph.get("saved-by", None)
            ontology_version = graph.graph.get("data-version", None)
            ontology_lastUpdated = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            ontology = Ontology(name=ontology_name, lastUpdated=ontology_lastUpdated, author=ontology_author,
                                version=ontology_version, generated=False)
        except Exception as e:
            print("error", e)

        return ontology.name

    def parse(self, notifications: Notifications):

        if self.ontology_file is None:
            self.obo_file.ontologies = self.ontolgies
            self.obo_file.terms = self.obo_file.terms
            self.obo_file.relationships = self.obo_file.relationships

            notifications.messages.append(Message(type="fail", message="Ontology could not be read"))



            return self.obo_file.dict()


        # try to read ontology file
        try:
            graph = obonet.read_obo(self.ontology_file, ignore_obsolete=False)

            typedefs = graph.graph.get("typedefs", None)

            for definition in typedefs:
                id = definition.get("id")
                if id not in self.typedefs:
                    self.typedefs[id] = definition.get("name")

            # print("typedefs", self.typedefs)


        except Exception as e:
            print(e)
            notifications.messages.append(Message(type="fail", message="Ontology could not be read"))
            # sys.exit()
            return

        try:
            ontology_name = graph.graph.get("name", None)
            ontology_author = graph.graph.get("saved-by", None)
            ontology_version = graph.graph.get("data-version", None)
            ontology_lastUpdated = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            treat_equivalent = graph.graph.get("treat-xrefs-as-equivalent", [])
            # print("equi", treat_equivalent)
            treat_as_relationship = graph.graph.get("treat-xrefs-as-relationship", [])
            # print("rela")
            treat_isa = graph.graph.get("treat-xrefs-as-is_a", [])

            treat_isa = [x.lower().split(" ") for x in treat_isa]
            # print("isa", treat_isa)
            treat_equivalent = [x.lower() for x in treat_equivalent]

            if treat_isa != []:
                treat_isa = treat_isa[-1]

            # print("adding: ", ontology_name)
            #
            # print("b")
            # print("treat equi", treat_equivalent)

            # if treat_equivalent != []:
            #     treat_equivalent = treat_equivalent[-1]

            # print("c")

            relationships_dict = dict()
            for treat in treat_as_relationship:
                # print("treat:", treat)
                relationships_dict = dict(x.lower().split(" ") for x in treat_as_relationship)

            ontology = Ontology(name=ontology_name, lastUpdated=ontology_lastUpdated, author=ontology_author,
                                version=ontology_version, generated=False)

            notifications.ontology_name = ontology.name

            self.obo_file.ontologies.append(ontology)
            self.collected_ontologies.add(ontology_name)
        except:
            notifications.messages.append(Message(type="fail", message="Ontology file does not comply with the "
                                                                       "guidelines"))

        try:
            nodes = graph.nodes
        except Exception as e:
            nodes = []

        # go through all nodes
        for node in nodes:

            # print("current node", node)

            # current_dict = dict()
            name = graph.nodes[node].get("name", None)
            definition = graph.nodes[node].get("def", None)
            is_obsolete = graph.nodes[node].get("is_obsolete", None)
            xref = graph.nodes[node].get("xref", None)

            # print("name", name)
            # print("current node is ", node)

            node_prefix = node.split(":")[0].lower().rstrip()
            accession = str(node).upper()
            term = Term(name=name, accession=accession, definition=definition, is_obsolete=is_obsolete,
                        ontology_origin=node_prefix)
            self.obo_file.terms.append(term)
            self.collected_terms.add(node)

            # add xrefs to relationships list
            # if xref:
            #     for x_reference in xref:
            #         node_prefix = x_reference.split(":")[0].lower().rstrip()
            #         ontology_lastUpdated = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            #         if not self.ontology_available(node_prefix):
            #             ontology = Ontology(name=node_prefix, lastUpdated=ontology_lastUpdated, author=None,
            #                                 version=None, generated=True)
            #             self.obo_file.ontologies.append(ontology)
            #
            #         rel_type = "xref"
            #         relationship = Relationships(node_from=node, node_to=x_reference, rel_type=rel_type)
            #
            #         if not self.term_available(x_reference):
            #             term = Term(name=None, accession=x_reference, definition=None, is_obsolete=None,
            #                         ontology_origin=node_prefix)
            #             self.obo_file.terms.append(term)
            #             self.obo_file.relationships.append(relationship)

            # node_prefix = node.split(":")[0].lower().rstrip()
            if not self.ontology_available(node_prefix):
                print("prefix", node_prefix)
                ontology = Ontology(name=node_prefix, lastUpdated=ontology_lastUpdated, author=None,
                                    version=None, generated=None, importedFrom=ontology_name)
                self.obo_file.ontologies.append(ontology)
                self.collected_ontologies.add(node_prefix)

            # ignore xrefs if no treat-header exists
            if xref and (treat_isa + treat_equivalent != [] or relationships_dict):
                # print("executing xref")
                for x_reference in xref:
                    node_prefix = x_reference.split(":")[0].lower().rstrip()

                    x_reference_accession = x_reference.upper()


                    ontology_lastUpdated = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                    if node_prefix in treat_isa:
                        if not self.term_available(x_reference):



                            term = Term(name=None, accession=x_reference_accession, definition=None, is_obsolete=None,
                                        ontology_origin=node_prefix)
                            self.obo_file.terms.append(term)
                        if not self.ontology_available(node_prefix):
                            ontology = Ontology(name=node_prefix, lastUpdated=ontology_lastUpdated, author=None,
                                                version=None, generated=None, importedFrom=ontology_name)
                            self.obo_file.ontologies.append(ontology)
                            self.collected_ontologies.add(node_prefix)

                        relationship = Relationships(node_from=node, node_to=x_reference_accession, rel_type="is_a")
                        self.obo_file.relationships.append(relationship)

                    if node_prefix in relationships_dict:
                        if not self.term_available(x_reference):
                            term = Term(name=None, accession=x_reference_accession, definition=None, is_obsolete=None,
                                        ontology_origin=node_prefix)
                            self.obo_file.terms.append(term)
                        if not self.ontology_available(node_prefix):
                            ontology = Ontology(name=node_prefix, lastUpdated=ontology_lastUpdated, author=None,
                                                version=None, generated=None, importedFrom=ontology_name)
                            self.obo_file.ontologies.append(ontology)
                            self.collected_ontologies.add(node_prefix)

                        relationship = Relationships(node_from=node, node_to=x_reference_accession,
                                                     rel_type=relationships_dict.get(node_prefix))
                        self.obo_file.relationships.append(relationship)

                    if node_prefix in treat_equivalent:
                        if not self.term_available(x_reference):
                            term = Term(name=None, accession=x_reference_accession, definition=None, is_obsolete=None,
                                        ontology_origin=node_prefix)
                            self.obo_file.terms.append(term)
                        if not self.ontology_available(node_prefix):
                            ontology = Ontology(name=node_prefix, lastUpdated=ontology_lastUpdated, author=None,
                                                version=None, generated=None, importedFrom=ontology_name)
                            self.obo_file.ontologies.append(ontology)
                            self.collected_ontologies.add(node_prefix)

                        relationship = Relationships(node_from=node, node_to=x_reference_accession,
                                                     rel_type="is_equivalent")
                        self.obo_file.relationships.append(relationship)
                        relationship = Relationships(node_from=x_reference_accession, node_to=node,
                                                     rel_type="is_equivalent")
                        self.obo_file.relationships.append(relationship)

            # search all child nodes of current node and add to relation list
            for child, parent, rel_type in graph.out_edges(node, keys=True):

                child_accession = str(child).upper()


                if rel_type in self.typedefs:
                    # print("typedef found", rel_type)
                    rel_type = self.typedefs.get(rel_type)

                relationship = Relationships(node_from=child_accession, node_to=parent, rel_type=rel_type)
                self.obo_file.relationships.append(relationship)

                if not self.term_available(child):
                    node_prefix = node.split(":")[0].lower().rstrip()

                    term = Term(name=None, accession=child_accession, definition=None, is_obsolete=None,
                                ontology_origin=node_prefix)
                    self.obo_file.terms.append(term)
                    self.obo_file.relationships.append(relationship)
                    self.collected_terms.add(child)

            # print("processing node ", node)

        # print("task", getrusage(RUSAGE_SELF).ru_maxrss * 4096 / 1024 /1024)

        # print(self.obo_file.dict())

        # print("parsing finished: " +ontology_name)
        # print("hashset", self.collected_ontologies)
        # print("hashset", self.collected_terms)
        # json.dump(self.obo_file.dict(), open( "obo.json", 'w' ) )
        print("parsing finished successfully")

        return self.obo_file.dict()
