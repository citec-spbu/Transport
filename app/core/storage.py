from typing import Dict
from app.core.context.analysis_context import AnalysisContext
from datetime import datetime, timezone

active_datasets: Dict[str, dict] = {}
# структура словаря:
# {
#   "dataset_id": {
#       "name": str,
#       "analysis_context": AnalysisContext,
#       "user_email": Optional[str],
#       "guest_token": Optional[str]
#   }
# }
