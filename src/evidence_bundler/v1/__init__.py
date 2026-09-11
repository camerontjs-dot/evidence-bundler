"""Research-backed maintained Evidence Bundler V1 candidate surface."""

from evidence_bundler.v1.builder import build_package
from evidence_bundler.v1.contract_a import (
    CONTRACT_A_VERSION,
    ContractAValidationError,
    load_contract_a,
    primary_targets,
    validate_contract_a,
)
from evidence_bundler.v1.package import (
    PACKAGE_CONTRACT_VERSION,
    PACKAGE_SCHEMA,
    EvidencePackageValidationError,
    V1Config,
    load_admission,
    load_package,
    validate_package,
    write_package,
)

__all__ = [
    "CONTRACT_A_VERSION",
    "PACKAGE_CONTRACT_VERSION",
    "PACKAGE_SCHEMA",
    "ContractAValidationError",
    "EvidencePackageValidationError",
    "V1Config",
    "build_package",
    "load_admission",
    "load_contract_a",
    "load_package",
    "primary_targets",
    "validate_contract_a",
    "validate_package",
    "write_package",
]
