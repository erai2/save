import os
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, CHAR
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_PATH = "mingli_analysis.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
Base = declarative_base()

# --- 1. 테이블 정의 (확장 필드 포함) ---
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
    analyses = relationship("Analysis", back_populates="case")
    fortunes = relationship("MajorFortune", back_populates="case")

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

class LukGod(Base):
    __tablename__ = "lukgod"
    god_id = Column(Integer, primary_key=True)
    celestial_stem = Column(CHAR(1))
    terrestrial_branch = Column(CHAR(1))
    description = Column(Text)

class MajorFortune(Base):
    __tablename__ = "majorfortune"
    fortune_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"))
    age = Column(Integer)
    celestial_stem = Column(CHAR(1))
    terrestrial_branch = Column(CHAR(1))
    fortune_analysis = Column(Text)
    case = relationship("Case", back_populates="fortunes")

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
    analyses = relationship("Analysis", back_populates="applied_rule")

# --- 2. DB 생성/초기화 함수 ---
def init_db():
    if not os.path.exists(DB_PATH):
        Base.metadata.create_all(engine)
        print("DB 초기화 완료:", DB_PATH)
    else:
        print("DB 파일 이미 존재:", DB_PATH)

# --- 3. 세션 준비 ---
Session = sessionmaker(bind=engine)
session = Session()

# --- 4. 예시 데이터 입력 ---
def insert_sample():
    # 룰 등록
    rule = WealthRules(
        rule_description="관인상생 구조의 재성 판정",
        application_conditions="격국=관인상생 AND 대운>=30",
        effect="재물운 상승, 혼인 가능",
        priority=100,
        exception_conditions="사주에 파재/파관 포함시 제외",
        applicable_scope="여성, 대운 30~50세, 관인상생",
        interpretation_method="관인→재성→대운→예외",
        note="관인상생+대운+재성 특별 케이스"
    )
    session.add(rule)
    session.commit()

    # 사례 등록
    case = Case(
        case_title="A 사례",
        birth_info="1990-01-01",
        celestial_stems="甲丙戊庚",
        terrestrial_branches="子午辰戌",
        structure_type="관인상생",
        empty_absence="申酉",
        major_fortune="30세~40세 甲辰대운",
        suppression_method="관인상생 구조"
    )
    session.add(case)
    session.commit()

    # 분석 등록
    analysis = Analysis(
        case_id=case.case_id,
        analysis_type="관인상생",
        description="관인상생 구조가 작용하여 학력과 관운이 모두 양호",
        applied_rule_id=rule.rule_id,
        priority=100,
        note="실제 대학 졸업 및 공무원 합격"
    )
    session.add(analysis)
    session.commit()

    # 대운 등록
    mf = MajorFortune(
        case_id=case.case_id,
        age=35,
        celestial_stem="甲",
        terrestrial_branch="辰",
        fortune_analysis="대운 甲辰에 관인상생의 영향 극대화"
    )
    session.add(mf)
    session.commit()

    # 록신 등록
    lg = LukGod(
        celestial_stem="甲",
        terrestrial_branch="子",
        description="甲의 祿神은 子로, 현실적 응기 작용이 강함"
    )
    session.add(lg)
    session.commit()

    print("샘플 데이터 등록 완료")

# --- 5. 예시 질의 ---
def show_query_demo():
    print("\n[사례별 분석 내역]")
    for case in session.query(Case).all():
        print(f"사례: {case.case_title} | {case.birth_info} | {case.structure_type}")
        for a in case.analyses:
            print("   -", a.analysis_type, "|", a.description, "| 룰:", a.applied_rule.rule_description if a.applied_rule else "-")
        for f in case.fortunes:
            print("   > 대운:", f.age, f.celestial_stem, f.terrestrial_branch, "|", f.fortune_analysis)
    print("\n[룰별 적용 사례]")
    for rule in session.query(WealthRules).all():
        print(f"룰: {rule.rule_description} | 적용분석:", len(rule.analyses))

if __name__ == "__main__":
    init_db()
    if not session.query(Case).count():
        insert_sample()
    show_query_demo()
