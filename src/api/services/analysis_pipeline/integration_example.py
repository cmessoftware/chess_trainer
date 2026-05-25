"""
V7 Pipeline Integration Example

Shows how to integrate the V7 pipeline with existing API endpoints.

Usage in API:
    from .services.analysis_pipeline import generate_validated_feedback, create_v7_repos
    
    @app.post("/api/analysis/v7-feedback")
    async def generate_v7_feedback_endpoint(
        request: GenerateFeedbackRequest,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        repos = create_v7_repos(db, models)
        llm_client = LLMClient()  # Your LLM client wrapper
        
        result = generate_validated_feedback(
            request.game_id,
            repos=repos,
            llm_client=llm_client,
            cp_loss_threshold=90,
            max_items=10,
        )
        
        return {
            "status": "success",
            "data": result,
        }
"""

from typing import Any, Dict
from sqlalchemy.orm import Session
from pydantic import BaseModel


class LLMClientWrapper:
    """
    Wrapper for LLM client compatible with V7 pipeline.
    
    Adapt this to your actual LLM client (OpenAI, Anthropic, Azure, etc.).
    """

    def __init__(self, client: Any):
        """
        Args:
            client: Your LLM client (e.g., OpenAI().chat.completions)
        """
        self.client = client

    def complete(self, prompt: str) -> str:
        """
        Generate completion for prompt.
        
        Args:
            prompt: Full prompt (system rules + user JSON)
        
        Returns:
            LLM text response
        """
        # Example for OpenAI:
        # response = self.client.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0.3,
        # )
        # return response.choices[0].message.content

        # Placeholder for now
        return (
            "Diagnosis: Error detectado (cp_loss alto)\n"
            "Better move: Considerar alternativa más sólida\n"
            "Training rule: Evaluar consecuencias antes de jugar"
        )


def integrate_v7_with_existing_service(
    db_session: Session,
    models: Any,
    game_id: str,
    llm_client: Any,
) -> Dict[str, Any]:
    """
    Integration helper for V7 pipeline with existing services.
    
    Args:
        db_session: SQLAlchemy session
        models: Module with Game, Features ORM models
        game_id: Game to analyze
        llm_client: Your LLM client
    
    Returns:
        V7 feedback result
    """
    from .analysis_pipeline import generate_validated_feedback, create_v7_repos

    # Create repository adapter
    repos = create_v7_repos(db_session, models)

    # Wrap LLM client
    wrapped_llm = LLMClientWrapper(llm_client)

    # Generate feedback
    result = generate_validated_feedback(
        game_id,
        repos=repos,
        llm_client=wrapped_llm,
        cp_loss_threshold=90,  # Adjust threshold as needed
        max_items=10,  # Limit critical moves
    )

    return result


def compare_v6_vs_v7(
    db_session: Session,
    models: Any,
    game_id: str,
    llm_client: Any,
    v6_service: Any,
) -> Dict[str, Any]:
    """
    A/B testing helper to compare V6 vs V7 outputs.
    
    Args:
        db_session: SQLAlchemy session
        models: ORM models
        game_id: Game to analyze
        llm_client: LLM client
        v6_service: Existing V6 LLM service
    
    Returns:
        {
          "v6": {...},
          "v7": {...},
          "comparison": {
            "num_critical_v6": ...,
            "num_critical_v7": ...,
            "disagreements": ...
          }
        }
    """
    # Generate V6 feedback
    v6_result = v6_service.generate_game_feedback(game_id)

    # Generate V7 feedback
    v7_result = integrate_v7_with_existing_service(
        db_session, models, game_id, llm_client
    )

    # Compare results
    v6_critical = len(v6_result.get("critical_moves", []))
    v7_critical = v7_result["stats"]["num_critical"]

    return {
        "v6": v6_result,
        "v7": v7_result,
        "comparison": {
            "num_critical_v6": v6_critical,
            "num_critical_v7": v7_critical,
            "disagreements": v7_result["stats"]["num_disagreements"],
        },
    }


# Example Pydantic request models for API

class GenerateFeedbackRequest(BaseModel):
    """Request model for V7 feedback endpoint."""

    game_id: str
    cp_loss_threshold: int = 90
    max_items: int = 10


class GenerateFeedbackResponse(BaseModel):
    """Response model for V7 feedback endpoint."""

    status: str
    data: Dict[str, Any]
    error: str = None


# Example FastAPI endpoint
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/analysis/v7-feedback", response_model=GenerateFeedbackResponse)
async def generate_v7_feedback(
    request: GenerateFeedbackRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    '''
    Generate validated feedback using V7 pipeline.
    
    V7 prevents hallucinations by:
    - Using only Stockfish ground truth (not buggy material_balance)
    - Cross-validating ML predictions
    - Conservative pattern detection
    - LLM only verbalizes pre-validated JSON
    '''
    try:
        repos = create_v7_repos(db, models)
        llm_client = LLMClientWrapper(openai_client)
        
        result = generate_validated_feedback(
            request.game_id,
            repos=repos,
            llm_client=llm_client,
            cp_loss_threshold=request.cp_loss_threshold,
            max_items=request.max_items,
        )
        
        return GenerateFeedbackResponse(
            status="success",
            data=result,
        )
    
    except ValueError as e:
        return GenerateFeedbackResponse(
            status="error",
            data={},
            error=str(e),
        )
"""
