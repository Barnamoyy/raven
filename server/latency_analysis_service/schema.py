from pydantic import BaseModel

class Latency_analysis(BaseModel):
    filename: str
    average_latency: float

class Latency_analysisCreate(Latency_analysisBase):
    pass

class Latency_analysisResponse(Latency_analysisBase):
    id: int

    class Config:
        from_attributes = True
