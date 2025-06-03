from pydantic import BaseModel
from langgraph.graph import StateGraph,END

class QuizQuestionGeneration(BaseModel):
    lesson_id:str


def searchQdrant():
    pass

def generateQuizQuestions():
    pass




def run_quiz_question_workflow():
    
    workflow=StateGraph(QuizQuestionGeneration)
    workflow.add_node("",)
    workflow.add_node("",)
    workflow.add_edge("","")
    workflow_compiled=workflow.compile()
    return workflow_compiled