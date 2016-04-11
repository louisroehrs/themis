"""
Get answers to questions from various Q&A systems.

WEA
    Extract answer from usage logs.

Solr
    Lookup answers from a Solr database using questions as queries.

NLC
    Train an NLC model to answer questions using the truth file downloaded from XMGR.
    1. train
    2. use
    3. list
    4. status
    5. delete
"""
import argparse

from themis import CsvFileType, ANSWER, ANSWER_ID, to_csv, pretty_print_json
from themis.nlc import train_nlc, NLC, classifier_list, classifier_status, remove_classifiers
from themis.test import answer_questions, Solr
from themis.wea import WeaLogFileType, ask_wea


def qa_command(subparsers):
    qa_shared_arguments = argparse.ArgumentParser(add_help=False)
    qa_shared_arguments.add_argument("questions", type=CsvFileType(),
                                     help="question set generated by the 'xmgr questions' command")
    qa_shared_arguments.add_argument("output", type=str, help="output filename")
    qa_shared_arguments.add_argument("--checkpoint-frequency", type=int, default=100,
                                     help="how often to flush to a checkpoint file")

    parser = subparsers.add_parser("qa", help="answer questions with Q&A systems")
    subparsers = parser.add_subparsers(title="Q&A", description="the various Q&A systems", help="Q&A systems")
    # Extract answers from the usage log.
    qa_wea = subparsers.add_parser("wea", parents=[qa_shared_arguments], help="extract WEA answers from usage log")
    qa_wea.add_argument("usage_log", type=WeaLogFileType(), help="QuestionsData.csv usage log file from XMGR")
    qa_wea.set_defaults(func=wea_handler)
    # Query answers from a Solr database.
    qa_solr = subparsers.add_parser("solr", parents=[qa_shared_arguments], help="query answers from a Solr database")
    qa_solr.add_argument("url", type=str, help="solr URL")
    qa_solr.set_defaults(func=solr_handler)
    # Manage an NLC model.
    nlc_shared_arguments = argparse.ArgumentParser(add_help=False)
    nlc_shared_arguments.add_argument("url", help="NLC url")
    nlc_shared_arguments.add_argument("username", help="NLC username")
    nlc_shared_arguments.add_argument("password", help="NLC password")

    nlc_parser = subparsers.add_parser("nlc", help="answer questions with NLC")
    nlc_subparsers = nlc_parser.add_subparsers(title="Natural Language Classifier",
                                               description="train, use, and manage NLC models", help="NLC actions")
    # Train NLC model.
    nlc_train = nlc_subparsers.add_parser("train", parents=[nlc_shared_arguments], help="train an NLC model")
    nlc_train.add_argument("truth", type=CsvFileType(), help="truth file created by the 'xmgr truth' command")
    nlc_train.add_argument("name", help="classifier name")
    nlc_train.set_defaults(func=nlc_train_handler)
    # Use an NLC model.
    nlc_use = nlc_subparsers.add_parser("use", parents=[nlc_shared_arguments, qa_shared_arguments],
                                        help="use NLC model")
    nlc_use.add_argument("classifier", help="classifier id")
    nlc_use.add_argument("corpus", type=CsvFileType([ANSWER, ANSWER_ID]),
                         help="corpus file created by the xmgr command")
    nlc_use.set_defaults(func=nlc_use_handler)
    # List all NLC models.
    nlc_list = nlc_subparsers.add_parser("list", parents=[nlc_shared_arguments], help="list NLC models")
    nlc_list.set_defaults(func=nlc_list_handler)
    # Get status of NLC models.
    nlc_status = nlc_subparsers.add_parser("status", parents=[nlc_shared_arguments], help="status of NLC model")
    nlc_status.add_argument("classifiers", nargs="+", help="classifier ids")
    nlc_status.set_defaults(func=nlc_status_handler)
    # Delete NLC models.
    nlc_delete = nlc_subparsers.add_parser("delete", parents=[nlc_shared_arguments], help="delete an NLC model")
    nlc_delete.add_argument("classifiers", nargs="+", help="classifier ids")
    nlc_delete.set_defaults(func=nlc_delete_handler)


def wea_handler(args):
    wea_answers = ask_wea(args.questions, args.usage_log)
    to_csv(args.output, wea_answers)


def solr_handler(args):
    answer_questions(Solr(args.url), args.questions, args.output, args.checkpoint_frequency)


def nlc_train_handler(args):
    print(train_nlc(args.url, args.username, args.password, args.truth, args.name))


def nlc_use_handler(args):
    corpus = args.corpus.set_index(ANSWER_ID)
    n = NLC(args.url, args.username, args.password, args.classifier, corpus)
    answer_questions(n, args.questions, args.output, args.checkpoint_frequency)


def nlc_list_handler(args):
    print(pretty_print_json(classifier_list(args.url, args.username, args.password)))


def nlc_status_handler(args):
    classifier_status(args.url, args.username, args.password, args.classifiers)


def nlc_delete_handler(args):
    remove_classifiers(args.url, args.username, args.password, args.classifiers)
