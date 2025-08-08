from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, CHAR
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_PATH = "mingli_analysis.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# --- 테이블 정의 (위에서 사용한 구조와 동일, 일부 축약) ---
class Case(Base):
    __tablename__ = "cases"
    case_id = Column(Integer, primary_key=True)
    case_title = Column(String(100))
    birth_info = Column(String(50))
    celestial_stems = Column(String(50))
    terrestrial_branches = Column(String(50))
    structure_type = Column(String(100))
    empty_absence = Column(String(50))
    major_fortune = Column(String(200))
    suppression_method = Column(String(100))
    analyses = relationship("Analysis", back_populates="case", cascade="all, delete-orphan")
    fortunes = relationship("MajorFortune", back_populates="case", cascade="all, delete-orphan")

class Analysis(Base):
    __tablename__ = "analysis"
    analysis_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"))
    analysis_type = Column(String(50))
    description = Column(Text)
    applied_rule_id = Column(Integer, ForeignKey("wealthrules.rule_id"))
    priority = Column(Integer, default=0)
    note = Column(Text)
    case = relationship("Case", back_populates="analyses")
    applied_rule = relationship("WealthRules", back_populates="analyses")

class WealthRules(Base):
    __tablename__ = "wealthrules"
    rule_id = Column(Integer, primary_key=True)
    rule_description = Column(Text)
    application_conditions = Column(Text)
    effect = Column(Text)
    priority = Column(Integer, default=0)
    exception_conditions = Column(Text)
    applicable_scope = Column(Text)
    interpretation_method = Column(Text)
    note = Column(Text)
    analyses = relationship("Analysis", back_populates="applied_rule", cascade="all, delete-orphan")

Base.metadata.create_all(engine)

# --- Pydantic Schemas ---
class CaseCreate(BaseModel):
    case_title: str
    birth_info: Optional[str] = ""
    celestial_stems: Optional[str] = ""
    terrestrial_branches: Optional[str] = ""
    structure_type: Optional[str] = ""
    empty_absence: Optional[str] = ""
    major_fortune: Optional[str] = ""
    suppression_method: Optional[str] = ""

class CaseOut(CaseCreate):
    case_id: int
    class Config:
        orm_mode = True

class WealthRuleCreate(BaseModel):
    rule_description: str
    application_conditions: Optional[str] = ""
    effect: Optional[str] = ""
    priority: Optional[int] = 0
    exception_conditions: Optional[str] = ""
    applicable_scope: Optional[str] = ""
    interpretation_method: Optional[str] = ""
    note: Optional[str] = ""

class WealthRuleOut(WealthRuleCreate):
    rule_id: int
    class Config:
        orm_mode = True

# --- FastAPI 앱 ---
app = FastAPI()

@app.post("/cases/", response_model=CaseOut)
def create_case(case: CaseCreate):
    session = Session()
    obj = Case(**case.dict())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    session.close()
    return obj

@app.get("/cases/", response_model=List[CaseOut])
def list_cases(q: Optional[str] = Query(None, description="검색어(제목/간지 등)")):
    session = Session()
    if q:
        objs = session.query(Case).filter(Case.case_title.contains(q) | Case.structure_type.contains(q)).all()
    else:
        objs = session.query(Case).all()
    session.close()
    return objs

@app.delete("/cases/{case_id}")
def delete_case(case_id: int):
    session = Session()
    obj = session.query(Case).filter_by(case_id=case_id).first()
    if not obj:
        session.close()
        raise HTTPException(status_code=404, detail="Case not found")
    session.delete(obj)
    session.commit()
    session.close()
    return {"ok": True}

@app.put("/cases/{case_id}", response_model=CaseOut)
def update_case(case_id: int, case: CaseCreate):
    session = Session()
    obj = session.query(Case).filter_by(case_id=case_id).first()
    if not obj:
        session.close()
        raise HTTPException(status_code=404, detail="Case not found")
    for k, v in case.dict().items():
        setattr(obj, k, v)
    session.commit()
    session.refresh(obj)
    session.close()
    return obj

# --- WealthRules(CRUD) ---
@app.post("/rules/", response_model=WealthRuleOut)
def create_rule(rule: WealthRuleCreate):
    session = Session()
    obj = WealthRules(**rule.dict())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    session.close()
    return obj

@app.get("/rules/", response_model=List[WealthRuleOut])
def list_rules(q: Optional[str] = Query(None, description="규칙 내용/적용조건 등 검색")):
    session = Session()
    if q:
        objs = session.query(WealthRules).filter(WealthRules.rule_description.contains(q)).all()
    else:
        objs = session.query(WealthRules).all()
    session.close()
    return objs

@app.delete("/rules/{rule_id}")
def delete_rule(rule_id: int):
    session = Session()
    obj = session.query(WealthRules).filter_by(rule_id=rule_id).first()
    if not obj:
        session.close()
        raise HTTPException(status_code=404, detail="Rule not found")
    session.delete(obj)
    session.commit()
    session.close()
    return {"ok": True}

@app.put("/rules/{rule_id}", response_model=WealthRuleOut)
def update_rule(rule_id: int, rule: WealthRuleCreate):
    session = Session()
    obj = session.query(WealthRules).filter_by(rule_id=rule_id).first()
    if not obj:
        session.close()
        raise HTTPException(status_code=404, detail="Rule not found")
    for k, v in rule.dict().items():
        setattr(obj, k, v)
    session.commit()
    session.refresh(obj)
    session.close()
    return obj

# 기타: Analysis, MajorFortune 등도 같은 패턴으로 확장하면 OK

# --- 앱 실행 (명령행에서) ---
# uvicorn main:app --reload

