"""
Judge answers using Annotate Assist

pairs
    Generate question and answer pairs for Annotation Assist to judge. This takes question list filter, system answers,
    optional previous annotations.

corpus
    Create the corpus file used by Annotation Assist.

interpret
    Apply judgement threshold to file retrieved from Annotation Assist.
"""
from themis import CsvFileType, QUESTION, print_csv
from themis.annotate import AnnotationAssistFileType, create_annotation_assist_corpus, annotation_assist_qa_input, \
    interpret_annotation_assist
from themis.xmgr import CorpusFileType


def judge_command(subparsers):
    judge_parser = subparsers.add_parser("judge", help="judge answers provided by Q&A systems")
    subparsers = judge_parser.add_subparsers(description="create and interpret files used by Annotation Assist")
    # Annotation Assistant Q&A pairs.
    judge_pairs = subparsers.add_parser("pairs",
                                        help="generate question and answer pairs for judgment by Annotation Assistant")
    judge_pairs.add_argument("answers", type=CsvFileType(), nargs="+",
                             help="answers generated by one of the 'answer' commands")
    judge_pairs.add_argument("--questions", type=CsvFileType([QUESTION]),
                             help="limit Q&A pairs to just these questions")
    judge_pairs.add_argument("--judgments", type=CsvFileType(), nargs="+",
                             help="Q&A pair judgments generated by the 'judge interpret' command")
    judge_pairs.set_defaults(func=pairs_handler)
    # Annotation Assistant corpus.
    judge_corpus = subparsers.add_parser("corpus", help="generate corpus file for Annotation Assistant")
    judge_corpus.add_argument("corpus", type=CorpusFileType(),
                              help="corpus file created by the 'download corpus' command")
    judge_corpus.set_defaults(func=corpus_handler)
    # Interpret Annotation Assistant judgments.
    judge_interpret = subparsers.add_parser("interpret", help="interpret Annotation Assistant judgments")
    judge_interpret.add_argument("judgments", type=AnnotationAssistFileType(),
                                 help="judgments file downloaded from Annotation Assistant")
    judge_interpret.add_argument("--judgment-threshold", metavar="JUDGMENT-THRESHOLD", type=float, default=50,
                                 help="cutoff value for a correct score, default 50")
    judge_interpret.set_defaults(func=interpret_handler)


def pairs_handler(args):
    qa_pairs = annotation_assist_qa_input(args.answers, args.questions, args.judgments)
    print_csv(qa_pairs, index=False)


def corpus_handler(args):
    print(create_annotation_assist_corpus(args.corpus))


def interpret_handler(args):
    judgments = interpret_annotation_assist(args.judgments, args.judgment_threshold)
    print_csv(judgments)
