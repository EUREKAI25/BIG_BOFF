"""
AUTOSITES — Base de données SQLite manifest-driven.

Schéma :
    projects → pages → sections → blocks (seed_json éditable)

Le manifest JSON est décomposé en lignes DB.
L'admin lit/écrit ces lignes. Le générateur les reconstruit en ManifestPage.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine, event
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

# ── DB path ───────────────────────────────────────────────────────────────────
HERE    = Path(__file__).parent
DB_PATH = HERE.parent / "data" / "autosites.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

# Activer foreign keys SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── ORM ───────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class ProjectDB(Base):
    """Un projet = un site (ex: presence_ia, sublym, etc.)"""
    __tablename__ = "projects"

    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug       = Column(String, unique=True, nullable=False)
    name       = Column(String, nullable=False)
    theme_json = Column(Text, default="{}")   # ThemePreset sérialisé
    created_at = Column(DateTime, default=datetime.utcnow)

    pages = relationship("PageDB", back_populates="project", cascade="all, delete-orphan")


class PageDB(Base):
    """Une page du site (homepage, landing, etc.)"""
    __tablename__ = "pages"

    id                    = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id            = Column(String, ForeignKey("projects.id"), nullable=False)
    slug                  = Column(String, nullable=False)   # ex: "home", "landing_paris_resto"
    page_type             = Column(String, nullable=False)   # homepage / landing / product / etc.
    lang                  = Column(String, default="fr")
    title                 = Column(String, default="")
    description           = Column(Text, default="")
    placeholder_context   = Column(Text, default="{}")      # JSON {ville, metier, price, ...}
    meta_json             = Column(Text, default="{}")
    enabled               = Column(Boolean, default=True)
    created_at            = Column(DateTime, default=datetime.utcnow)

    project  = relationship("ProjectDB", back_populates="pages")
    sections = relationship("SectionDB", back_populates="page",
                            cascade="all, delete-orphan", order_by="SectionDB.order_index")


class SectionDB(Base):
    """Une section d'une page (hero, stats, steps, faq, etc.)"""
    __tablename__ = "sections"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id     = Column(String, ForeignKey("pages.id"), nullable=False)
    key         = Column(String, nullable=False)    # identifiant unique par page (snake_case)
    order_index = Column(Integer, default=0)
    enabled     = Column(Boolean, default=True)
    bg_color    = Column(String, nullable=True)
    layout_type = Column(String, nullable=True)     # full / two_col / asym_8_4 / null
    anchor_id   = Column(String, nullable=True)     # HTML id pour ancres nav

    page   = relationship("PageDB", back_populates="sections")
    blocks = relationship("BlockDB", back_populates="section",
                          cascade="all, delete-orphan", order_by="BlockDB.column_span.desc()")


class BlockDB(Base):
    """Un bloc dans une colonne de section."""
    __tablename__ = "blocks"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id     = Column(String, ForeignKey("sections.id"), nullable=False)
    column_span    = Column(Integer, default=12)
    block_type     = Column(String, nullable=False)   # hero_block / stat_block / etc.
    structure_json = Column(Text, default="{}")       # config non-éditable (bg_type, direction...)
    seed_json      = Column(Text, default="{}")       # CONTENU ÉDITABLE
    css_class      = Column(String, nullable=True)
    html_id        = Column(String, nullable=True)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    section = relationship("SectionDB", back_populates="blocks")


# ── Init ──────────────────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)


# ── Helpers manifest ──────────────────────────────────────────────────────────

def import_manifest_json(db: Session, project_slug: str, project_name: str,
                          manifest_path: Path) -> PageDB:
    """
    Importe un manifest JSON dans la DB.
    Crée le projet si inexistant.
    Remplace la page si le slug existe déjà.
    """
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Projet
    project = db.query(ProjectDB).filter_by(slug=project_slug).first()
    if not project:
        project = ProjectDB(slug=project_slug, name=project_name,
                            theme_json=json.dumps(raw.get("theme", {})))
        db.add(project)
        db.flush()
    else:
        # Mettre à jour le thème si présent
        if raw.get("theme"):
            project.theme_json = json.dumps(raw["theme"])

    # Supprimer page existante avec même slug
    page_slug = manifest_path.stem
    existing = db.query(PageDB).filter_by(project_id=project.id, slug=page_slug).first()
    if existing:
        db.delete(existing)
        db.flush()

    # Créer page
    page = PageDB(
        project_id          = project.id,
        slug                = page_slug,
        page_type           = raw.get("page_type", "landing"),
        lang                = raw.get("lang", "fr"),
        title               = raw.get("title", ""),
        description         = raw.get("description", ""),
        placeholder_context = json.dumps(raw.get("placeholder_context", {})),
        meta_json           = json.dumps(raw.get("meta", {})),
    )
    db.add(page)
    db.flush()

    # Sections et blocs
    for sec_raw in sorted(raw.get("sections", []), key=lambda s: s.get("order", 0)):
        section = SectionDB(
            page_id     = page.id,
            key         = sec_raw["key"],
            order_index = sec_raw.get("order", 0),
            enabled     = sec_raw.get("enabled", True),
            bg_color    = sec_raw.get("bg_color"),
            layout_type = sec_raw.get("layout_type"),
            anchor_id   = sec_raw.get("id"),
        )
        db.add(section)
        db.flush()

        for col_raw in sec_raw.get("columns", []):
            blk = col_raw.get("block", {})
            block = BlockDB(
                section_id     = section.id,
                column_span    = col_raw.get("span", 12),
                block_type     = blk.get("block_type", ""),
                structure_json = json.dumps(blk.get("structure", {})),
                seed_json      = json.dumps(blk.get("seed", {})),
                css_class      = blk.get("css_class"),
                html_id        = blk.get("id"),
            )
            db.add(block)

    db.commit()
    return page


def build_manifest_dict(db: Session, page_id: str) -> dict:
    """
    Reconstruit un dict ManifestPage depuis la DB.
    Utilisé par le générateur et le preview.
    """
    page = db.query(PageDB).filter_by(id=page_id).first()
    if not page:
        raise ValueError(f"Page introuvable : {page_id}")

    project = page.project
    theme   = json.loads(project.theme_json) if project.theme_json else {}

    sections = []
    for sec in page.sections:
        if not sec.enabled:
            continue
        columns = []
        for blk in sec.blocks:
            columns.append({
                "span": blk.column_span,
                "block": {
                    "block_type": blk.block_type,
                    "structure":  json.loads(blk.structure_json or "{}"),
                    "seed":       json.loads(blk.seed_json or "{}"),
                    "css_class":  blk.css_class,
                    "id":         blk.html_id,
                },
            })
        sections.append({
            "key":         sec.key,
            "enabled":     sec.enabled,
            "order":       sec.order_index,
            "id":          sec.anchor_id,
            "bg_color":    sec.bg_color,
            "layout_type": sec.layout_type,
            "columns":     columns,
        })

    return {
        "page_type":           page.page_type,
        "lang":                page.lang,
        "title":               page.title,
        "description":         page.description,
        "theme":               theme,
        "sections":            sections,
        "placeholder_context": json.loads(page.placeholder_context or "{}"),
        "meta":                json.loads(page.meta_json or "{}"),
    }
