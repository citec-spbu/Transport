from typing import Dict
from uuid import UUID
from app.core.context.analysis_context import AnalysisContext
from datetime import datetime, timezone

active_datasets: Dict[UUID, dict] = {}
# структура словаря:
# {
#   "dataset_id": {
#       "name": str,
#       "city_name": str,
#       "transport_type": str,
#       "analysis_context": AnalysisContext,
#       "user_id": Optional[UUID],
#       "guest_token": Optional[str]
#   }
# }
