import pandas as pd
import os
import targetBN
import numpy as np
import matplotlib.pyplot as plt

# Each function for structure learning
# Search method: Hill-Climbing
def Hill_Climbing(dataset: pd.DataFrame):
    # from pgmpy.estimators import ExhaustiveSearch
    from pgmpy.estimators import HillClimbSearch
    from pgmpy.estimators import BDeuScore, K2Score, BicScore
    from pgmpy.models import BayesianModel

    bdeu = BDeuScore(dataset, equivalent_sample_size=5)
    # k2 = K2Score(dataset)
    # bic = BicScore(dataset)

    # `K2Score`, `BDeuScore`, or `BicScore`
    # class BDeuScore(StructureScore):
    # def __init__(self, data, equivalent_sample_size=10, **kwargs):

    # class BicScore(StructureScore):
    # def __init__(self, data, **kwargs):

    # class K2Score(StructureScore):
    # def __init__(self, data, **kwargs):

    
    hc = HillClimbSearch(dataset, scoring_method=BDeuScore(dataset, equivalent_sample_size=5))
    iter_list = [2**i for i in range(100)]
    print(iter_list)
    for iteration in iter_list:
        DAG_connection = hc.estimate(max_iter=iteration)
        model = BayesianModel(DAG_connection.edges())
        print(bdeu.score(model))
    # hc = HillClimbSearch(dataset, scoring_method=BicScore(dataset))
    best_model = hc.estimate()
    # print(best_model.edges())
    return best_model.edges()


# Search method: Constraint-based
def Constraint_based(dataset: pd.DataFrame):
    from pgmpy.estimators import ConstraintBasedEstimator

    est = ConstraintBasedEstimator(dataset)

    # Construct dag
    skel, seperating_sets = est.estimate_skeleton(significance_level=0.01)
    print("Undirected edges:", skel.edges())

    pdag = est.skeleton_to_pdag(skel, seperating_sets)
    print("PDAG edges:", pdag.edges())

    model = est.pdag_to_dag(pdag)
    print("DAG edges:", model.edges())

    # print(est.estimate(significance_level=0.01).edges())
    print(type(model))


# Search method: Hybrid structure learning
def Hybrid(dataset: pd.DataFrame):
    from pgmpy.estimators import MmhcEstimator
    from pgmpy.estimators import HillClimbSearch
    from pgmpy.estimators import BDeuScore, K2Score, BicScore
    from pgmpy.models import BayesianModel
    
    mmhc = MmhcEstimator(dataset)
    # The mmhc method takes a parameter significance_level(default=0.01) the desired Type 1 error probability of
    # falsely rejecting the null hypothesis that variables. That is, confining Type 1 error rate.
    # (Therefore, the lower value, the less we are gonna accept dependencies, resulting in a sparser graph.)
    skeleton = mmhc.mmpc()
    print("Part 1) Skeleton: ", skeleton.edges())

    # use hill climb search to orient the edges:
    hc = HillClimbSearch(dataset, scoring_method=BDeuScore(dataset, equivalent_sample_size=5))
    # Recording the evaluation of different iteration
    bdeu = BDeuScore(dataset, equivalent_sample_size=5)
    iter_list = [2**i for i in range(20)]
    eval_list = []
    for iteration in iter_list:
        DAG_connection = hc.estimate(tabu_length=10, white_list=skeleton.to_directed().edges(), max_iter=iteration)
        model = BayesianModel(DAG_connection.edges())
        print(bdeu.score(model))
        eval_list.append(bdeu.score(model))

    print("Part 2) Model:    ", model.edges())
    return model.edges(), [iter_list, eval_list]

# File path
access_rights = 0o755
data_dir = "dataset"
data_fname = data_dir + "/Covid-19-dataset.pxl"
model_dir = "model"
model_name = model_dir + "/Learnt_model"

# Generate a dataset or open a stored one
# size of dataset
sample_size = 300000

if __name__== "__main__":
    if(not os.path.exists(model_dir)):
        try:
            os.mkdir(model_dir, access_rights)
        except OSError:
            print("Permission denied: creating directory=>", model_dir)
        else:
            print("Successfully create directory for dataset!")

    if(not os.path.exists(data_fname)):
        if(not os.path.exists(data_dir)):
            try:
                os.mkdir(data_dir, access_rights)
            except OSError:
                print("Permission denied: creating directory=>", data_dir)
            else:
                print("Successfully create directory for dataset!")

        generator = targetBN.TargetBayesNet(model_path=model_dir)
        dataset = generator.getDataset(sample_size)
        dataset.to_pickle(data_fname)
    else:
        dataset = pd.read_pickle(data_fname)
        # Once the sampling size changes, recreate the dataset againg
        if(len(dataset.index) != sample_size):
            generator = targetBN.TargetBayesNet(model_path=model_dir)
            dataset = generator.getDataset(sample_size)
            dataset.to_pickle(data_fname)
            
    # print(dataset)

    edges, progress_list = Hybrid(dataset)

    targetBN.saveGraphToPDF(model_name, list(edges), True)


    plt.plot(progress_list[0], progress_list[1], 'o-')
    plt.title('Evaluation from scoring function')
    plt.ylabel('Evaluation')
    plt.xlabel('Iteration')
    plt.xscale('log', basex=2)
    plt.tight_layout()

    plt.show()

    # Starting with defining the network structure
    # Creating the model as well as the structure (arcs)
    from pgmpy.models import BayesianModel

    # create a new BN
    covid_model = BayesianModel(edges)

    # Estimating the CPTs from the given dataset
    covid_model.fit(dataset)

    # Checking if the cpds are valid for the model.
    print("Checking if CPDs are valid for model: ", covid_model.check_model())

    # # Probability reasoning-----------------------------------
    # from pgmpy.inference import VariableElimination
    # covid_infer = VariableElimination(covid_model)

    # # Computing the probability of bronc given smoke.
    # q = covid_infer.query(variables=["Covid"], evidence={"Fever": 1})
    # print(q)

    # q = covid_infer.query(variables=["Covid"], evidence={"Fever": 1, "Difficulty_in_Breathing": 1})
    # print(q)

    # # Given the result of cancer, find P(+f|+c)
    # q = covid_infer.query(variables=["Fever"], evidence={"Covid": 1})
    # print(q)

    # q = covid_infer.query(variables=["Covid"], evidence={})
    # print(q)

    # q = covid_infer.query(variables=["Covid"], evidence={"Fever": 0, "Difficulty_in_Breathing": 0, "Tiredness": 1, "Dry_Cough": 0})
    # print(q)
