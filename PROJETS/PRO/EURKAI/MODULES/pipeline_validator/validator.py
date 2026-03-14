"""
PipelineValidator — algorithme de prévalidation de pipeline.

Logique totalement externe aux modules.
Entrée  : liste ordonnée de module_ids
Sortie  : PipelineValidationResult
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from .contracts import ContractRegistry


# ---------------------------------------------------------------------------
# Modèles de réponse
# ---------------------------------------------------------------------------

@dataclass
class TransitionResult:
    from_module:  str
    to_module:    str
    shared_datas: List[str]       # outputs(A) ∩ inputs(B)


@dataclass
class BreakResult:
    break_index:  int             # index de la transition cassée (0-based)
    from_module:  str
    to_module:    str
    outputs:      List[str]       # ce que from_module produit
    expected_inputs: List[str]    # ce que to_module attend
    shared_datas: List[str]       # [] — vide par définition
    suggestions:  List[str]       # modules compatibles directs depuis from_module
    bridges:      List[str]       # modules qui peuvent s'insérer entre les deux


@dataclass
class PipelineReport:
    """Résumé du pipeline — produit même si valide."""
    modules:        List[str]
    data_types_used: List[str]    # tous les types qui circulent
    has_sink:       bool          # le dernier module produit quelque chose d'utile
    terminal_outputs: List[str]   # outputs du dernier module


@dataclass
class PipelineValidationResult:
    valid:       bool
    transitions: List[TransitionResult] = field(default_factory=list)
    error:       Optional[str]          = None   # "pipeline_break" | "unknown_module" | ...
    break_info:  Optional[BreakResult]  = None
    report:      Optional[PipelineReport] = None


# ---------------------------------------------------------------------------
# Validateur
# ---------------------------------------------------------------------------

class PipelineValidator:

    def __init__(self, registry: ContractRegistry):
        self._registry = registry

    def validate(self, module_ids: List[str]) -> PipelineValidationResult:
        """
        Valide une séquence de modules.

        Algorithme :
            Pour chaque paire consécutive (module[i], module[i+1]) :
                shared = outputs(module[i]) ∩ inputs(module[i+1])
                si shared == ∅ → pipeline cassé à l'index i

        Complexité : O(n) avec n = len(module_ids) - 1
        """

        if not module_ids:
            return PipelineValidationResult(valid=False, error="empty_pipeline")

        if len(module_ids) == 1:
            try:
                contract = self._registry.get(module_ids[0])
            except KeyError as e:
                return PipelineValidationResult(valid=False, error="unknown_module",
                                                break_info=BreakResult(
                                                    break_index=0,
                                                    from_module=module_ids[0],
                                                    to_module="",
                                                    outputs=[], expected_inputs=[],
                                                    shared_datas=[], suggestions=[], bridges=[]
                                                ))
            report = self._build_report(module_ids, [])
            return PipelineValidationResult(valid=True, report=report)

        transitions: List[TransitionResult] = []

        for i in range(len(module_ids) - 1):
            mod_a_id = module_ids[i]
            mod_b_id = module_ids[i + 1]

            # Résolution des contrats — peut lever KeyError si module inconnu
            try:
                contract_a = self._registry.get(mod_a_id)
            except KeyError:
                return PipelineValidationResult(
                    valid=False,
                    error="unknown_module",
                    break_info=BreakResult(
                        break_index=i,
                        from_module=mod_a_id,
                        to_module=mod_b_id,
                        outputs=[], expected_inputs=[],
                        shared_datas=[], suggestions=[], bridges=[]
                    )
                )

            try:
                contract_b = self._registry.get(mod_b_id)
            except KeyError:
                return PipelineValidationResult(
                    valid=False,
                    error="unknown_module",
                    break_info=BreakResult(
                        break_index=i,
                        from_module=mod_a_id,
                        to_module=mod_b_id,
                        outputs=contract_a.output_datas, expected_inputs=[],
                        shared_datas=[], suggestions=[], bridges=[]
                    )
                )

            # Intersection
            outputs_a = set(contract_a.output_datas)
            inputs_b  = set(contract_b.input_datas)
            shared    = sorted(outputs_a & inputs_b)

            if not shared:
                # Pipeline cassé — calculer suggestions et bridges
                suggestions = self._registry.compatible_next(mod_a_id)
                bridges     = self._registry.bridges(mod_a_id, mod_b_id)

                return PipelineValidationResult(
                    valid=False,
                    error="pipeline_break",
                    break_info=BreakResult(
                        break_index=i,
                        from_module=mod_a_id,
                        to_module=mod_b_id,
                        outputs=sorted(outputs_a),
                        expected_inputs=sorted(inputs_b),
                        shared_datas=[],
                        suggestions=suggestions,
                        bridges=bridges,
                    )
                )

            transitions.append(TransitionResult(
                from_module=mod_a_id,
                to_module=mod_b_id,
                shared_datas=shared,
            ))

        report = self._build_report(module_ids, transitions)
        return PipelineValidationResult(valid=True, transitions=transitions, report=report)

    def _build_report(self,
                      module_ids: List[str],
                      transitions: List[TransitionResult]) -> PipelineReport:
        """Construit le rapport de synthèse du pipeline."""
        all_types: set = set()
        for t in transitions:
            all_types.update(t.shared_datas)

        last_contract    = self._registry.get(module_ids[-1])
        terminal_outputs = last_contract.output_datas
        has_sink         = bool(terminal_outputs)

        return PipelineReport(
            modules          = module_ids,
            data_types_used  = sorted(all_types),
            has_sink         = has_sink,
            terminal_outputs = terminal_outputs,
        )
