from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class StepPattern:
    label: str
    pattern: str
    domain: str


@dataclass(frozen=True)
class ErrorSignature:
    name: str
    root_cause: str
    keywords: List[str]
    confidence: float
    allowed_steps: Optional[Set[str]] = None
    domain: Optional[str] = None


STEP_KNOWLEDGE: List[StepPattern] = [
    StepPattern("pip install", r"\b(?:python\s+-m\s+)?pip\s+install\b", "package"),
    StepPattern("npm install", r"\bnpm\s+(?:ci|install)\b", "package"),
    StepPattern("yarn install", r"\byarn\s+install\b", "package"),
    StepPattern("poetry install", r"\bpoetry\s+install\b", "package"),
    StepPattern("docker build", r"\bdocker\s+(?:buildx\s+build|build)\b", "container"),
    StepPattern("docker pull", r"\bdocker\s+pull\b", "container"),
    StepPattern("docker push", r"\bdocker\s+push\b", "container"),
    StepPattern("docker login", r"\bdocker\s+login\b", "container"),
    StepPattern("helm install", r"\bhelm\s+install\b", "kubernetes"),
    StepPattern("helm upgrade", r"\bhelm\s+upgrade\b", "kubernetes"),
    StepPattern("helm rollback", r"\bhelm\s+rollback\b", "kubernetes"),
    StepPattern("helm uninstall", r"\bhelm\s+uninstall\b", "kubernetes"),
    StepPattern("helm lint", r"\bhelm\s+lint\b", "kubernetes"),
    StepPattern("helm template", r"\bhelm\s+template\b", "kubernetes"),
    StepPattern("kubectl apply", r"\bkubectl\s+apply\b", "kubernetes"),
    StepPattern("kubectl rollout", r"\bkubectl\s+rollout\b", "kubernetes"),
    StepPattern("kubectl get", r"\bkubectl\s+get\b", "kubernetes"),
    StepPattern("kubectl describe", r"\bkubectl\s+describe\b", "kubernetes"),
    StepPattern("kubectl logs", r"\bkubectl\s+logs\b", "kubernetes"),
    StepPattern("kubectl exec", r"\bkubectl\s+exec\b", "kubernetes"),
    StepPattern("kubectl scale", r"\bkubectl\s+scale\b", "kubernetes"),
    StepPattern("kubectl patch", r"\bkubectl\s+patch\b", "kubernetes"),
    StepPattern("kubectl delete", r"\bkubectl\s+delete\b", "kubernetes"),
    StepPattern("kubectl wait", r"\bkubectl\s+wait\b", "kubernetes"),
    StepPattern("kubectl set image", r"\bkubectl\s+set\s+image\b", "kubernetes"),
    StepPattern("kustomize build", r"\bkustomize\s+build\b", "kubernetes"),
    StepPattern("terraform init", r"\bterraform\s+init\b", "terraform"),
    StepPattern("terraform validate", r"\bterraform\s+validate\b", "terraform"),
    StepPattern("terraform fmt", r"\bterraform\s+fmt\b", "terraform"),
    StepPattern("terraform plan", r"\bterraform\s+plan\b", "terraform"),
    StepPattern("terraform apply", r"\bterraform\s+apply\b", "terraform"),
    StepPattern("terraform destroy", r"\bterraform\s+destroy\b", "terraform"),
    StepPattern("terraform import", r"\bterraform\s+import\b", "terraform"),
    StepPattern("terraform refresh", r"\bterraform\s+refresh\b", "terraform"),
    StepPattern("terraform workspace", r"\bterraform\s+workspace\b", "terraform"),
    StepPattern("ansible-playbook", r"\bansible-playbook\b", "ansible"),
    StepPattern("ansible", r"\bansible\b", "ansible"),
    StepPattern("ansible-galaxy", r"\bansible-galaxy\b", "ansible"),
    StepPattern("ansible-vault", r"\bansible-vault\b", "ansible"),
    StepPattern("git clone", r"\bgit\s+clone\b", "git"),
    StepPattern("git fetch", r"\bgit\s+fetch\b", "git"),
    StepPattern("git pull", r"\bgit\s+pull\b", "git"),
    StepPattern("git push", r"\bgit\s+push\b", "git"),
    StepPattern("git checkout", r"\bgit\s+checkout\b", "git"),
]

STEP_DOMAIN_MAP: Dict[str, str] = {step.label: step.domain for step in STEP_KNOWLEDGE}

CAUSAL_MAPPING: Dict[str, Dict[str, Set[str]]] = {
    "DEPENDENCY_ERROR": {
        "origin_steps": {"pip install", "npm install", "yarn install", "poetry install"}
    },
    "K8S_DEFAULT": {
        "origin_steps": {
            "kubectl apply",
            "kubectl rollout",
            "kubectl get",
            "kubectl describe",
            "kubectl logs",
            "kubectl exec",
            "kubectl delete",
            "kubectl scale",
            "kubectl patch",
            "kubectl set image",
            "kubectl wait",
            "kustomize build",
            "helm install",
            "helm upgrade",
            "helm rollback",
            "helm uninstall",
            "helm lint",
            "helm template"
        }
    },
    "TERRAFORM_DEFAULT": {
        "origin_steps": {
            "terraform init",
            "terraform validate",
            "terraform fmt",
            "terraform plan",
            "terraform apply",
            "terraform destroy",
            "terraform import",
            "terraform refresh",
            "terraform workspace"
        }
    },
    "ANSIBLE_DEFAULT": {
        "origin_steps": {"ansible-playbook", "ansible", "ansible-galaxy", "ansible-vault"}
    },
    "GIT_DEFAULT": {
        "origin_steps": {"git clone", "git fetch", "git pull", "git push", "git checkout"}
    },
}

CAUSAL_PREFIX_MAP: List[Tuple[str, str]] = [
    ("K8S_", "K8S_DEFAULT"),
    ("TERRAFORM_", "TERRAFORM_DEFAULT"),
    ("ANSIBLE_", "ANSIBLE_DEFAULT"),
    ("GIT_", "GIT_DEFAULT"),
]

ERROR_SIGNATURES: List[ErrorSignature] = [
    ErrorSignature(
        name="dependency_missing",
        root_cause="DEPENDENCY_ERROR",
        keywords=[
            "could not find a version",
            "no matching distribution",
            "requirements.txt",
            "package.json",
            "lockfile",
            "could not resolve dependency"
        ],
        confidence=0.8,
        allowed_steps=CAUSAL_MAPPING["DEPENDENCY_ERROR"]["origin_steps"],
        domain="package"
    ),
    ErrorSignature(
        name="k8s_image_pull",
        root_cause="K8S_IMAGE_PULL_ERROR",
        keywords=[
            "imagepullbackoff",
            "errimagepull",
            "failed to pull image",
            "pull access denied",
            "back-off pulling image",
            "unauthorized: authentication required",
            "manifest unknown"
        ],
        confidence=0.75,
        domain="kubernetes"
    ),
    ErrorSignature(
        name="k8s_crashloop",
        root_cause="K8S_CRASHLOOP_ERROR",
        keywords=[
            "crashloopbackoff",
            "back-off restarting failed container"
        ],
        confidence=0.72,
        domain="kubernetes"
    ),
    ErrorSignature(
        name="k8s_probe_failed",
        root_cause="K8S_PROBE_FAILED",
        keywords=[
            "readiness probe failed",
            "liveness probe failed",
            "startup probe failed"
        ],
        confidence=0.7,
        domain="kubernetes"
    ),
    ErrorSignature(
        name="k8s_volume_mount",
        root_cause="K8S_VOLUME_MOUNT_ERROR",
        keywords=[
            "failedmount",
            "mountvolume.setup failed",
            "failed to attach volume",
            "failed to mount",
            "persistentvolumeclaim",
            "pod has unbound immediate persistentvolumeclaims"
        ],
        confidence=0.7,
        domain="kubernetes"
    ),
    ErrorSignature(
        name="k8s_scheduling",
        root_cause="K8S_SCHEDULING_ERROR",
        keywords=[
            "failed scheduling",
            "insufficient cpu",
            "insufficient memory",
            "node(s) had taint",
            "nodes are available"
        ],
        confidence=0.7,
        domain="kubernetes"
    ),
    ErrorSignature(
        name="k8s_deploy_timeout",
        root_cause="K8S_DEPLOY_TIMEOUT",
        keywords=[
            "exceeded its progress deadline",
            "progress deadline exceeded",
            "timed out waiting for the condition"
        ],
        confidence=0.7,
        domain="kubernetes"
    ),
    ErrorSignature(
        name="k8s_rbac",
        root_cause="K8S_RBAC_ERROR",
        keywords=[
            "is forbidden",
            "forbidden",
            "cannot create resource",
            "cannot get resource",
            "cannot list resource",
            "cannot update resource",
            "cannot delete resource"
        ],
        confidence=0.72,
        domain="kubernetes"
    ),
    ErrorSignature(
        name="k8s_validation",
        root_cause="K8S_CONFIG_ERROR",
        keywords=[
            "error validating",
            "validation failed",
            "no matches for kind",
            "unknown field",
            "unable to recognize"
        ],
        confidence=0.68,
        domain="kubernetes"
    ),
    ErrorSignature(
        name="terraform_auth",
        root_cause="TERRAFORM_AUTH_ERROR",
        keywords=[
            "accessdeniedexception",
            "unauthorizedoperation",
            "invalidclienttokenid",
            "no valid credential sources found",
            "failed to get credentials"
        ],
        confidence=0.75,
        domain="terraform"
    ),
    ErrorSignature(
        name="terraform_state_lock",
        root_cause="TERRAFORM_STATE_LOCK",
        keywords=[
            "error acquiring the state lock",
            "state lock",
            "conditionalcheckfailedexception"
        ],
        confidence=0.75,
        domain="terraform"
    ),
    ErrorSignature(
        name="terraform_provider",
        root_cause="TERRAFORM_PROVIDER_ERROR",
        keywords=[
            "provider produced inconsistent result",
            "failed to instantiate provider",
            "plugin did not respond",
            "error configuring provider",
            "timeout while waiting for plugin"
        ],
        confidence=0.72,
        domain="terraform"
    ),
    ErrorSignature(
        name="terraform_validate",
        root_cause="TERRAFORM_VALIDATION_ERROR",
        keywords=[
            "unsupported argument",
            "reference to undeclared input variable",
            "invalid index",
            "invalid function argument",
            "invalid value for",
            "invalid configuration"
        ],
        confidence=0.7,
        domain="terraform"
    ),
    ErrorSignature(
        name="terraform_init",
        root_cause="TERRAFORM_INIT_ERROR",
        keywords=[
            "terraform init failed",
            "failed to download",
            "registry.terraform.io",
            "checksum mismatch"
        ],
        confidence=0.68,
        domain="terraform"
    ),
    ErrorSignature(
        name="terraform_apply",
        root_cause="TERRAFORM_APPLY_ERROR",
        keywords=[
            "terraform apply failed",
            "error applying",
            "error: failed to create",
            "error: failed to update",
            "error: failed to delete"
        ],
        confidence=0.68,
        domain="terraform"
    ),
    ErrorSignature(
        name="ansible_unreachable",
        root_cause="ANSIBLE_UNREACHABLE",
        keywords=[
            "unreachable!",
            "failed to connect",
            "connection timed out",
            "no route to host",
            "connection refused"
        ],
        confidence=0.72,
        domain="ansible"
    ),
    ErrorSignature(
        name="ansible_auth",
        root_cause="ANSIBLE_AUTH_ERROR",
        keywords=[
            "permission denied",
            "authentication failure",
            "ssh: handshake failed"
        ],
        confidence=0.7,
        domain="ansible"
    ),
    ErrorSignature(
        name="ansible_syntax",
        root_cause="ANSIBLE_SYNTAX_ERROR",
        keywords=[
            "syntax error",
            "could not parse",
            "yaml",
            "mapping values are not allowed"
        ],
        confidence=0.68,
        domain="ansible"
    ),
    ErrorSignature(
        name="ansible_task_failed",
        root_cause="ANSIBLE_TASK_FAILED",
        keywords=[
            "failed!",
            "fatal:"
        ],
        confidence=0.65,
        domain="ansible"
    ),
    ErrorSignature(
        name="prometheus_scrape",
        root_cause="PROMETHEUS_SCRAPE_ERROR",
        keywords=[
            "error scraping",
            "scrape failed",
            "scrape error",
            "context deadline exceeded"
        ],
        confidence=0.6,
        domain="prometheus"
    ),
    ErrorSignature(
        name="prometheus_remote_write",
        root_cause="PROMETHEUS_REMOTE_WRITE_ERROR",
        keywords=[
            "remote write",
            "failed to send samples",
            "server returned http status"
        ],
        confidence=0.6,
        domain="prometheus"
    ),
    ErrorSignature(
        name="loki_ingest",
        root_cause="LOKI_INGEST_ERROR",
        keywords=[
            "error sending batch",
            "failed to send batch",
            "failed to flush",
            "push request failed",
            "ingester"
        ],
        confidence=0.6,
        domain="loki"
    ),
    ErrorSignature(
        name="grafana_datasource",
        root_cause="GRAFANA_DATASOURCE_ERROR",
        keywords=[
            "failed to connect to datasource",
            "data source not found",
            "datasource",
            "unauthorized data source"
        ],
        confidence=0.6,
        domain="grafana"
    ),
    ErrorSignature(
        name="grafana_provision",
        root_cause="GRAFANA_PROVISIONING_ERROR",
        keywords=[
            "failed to provision",
            "provisioning",
            "dashboard provisioning failed"
        ],
        confidence=0.6,
        domain="grafana"
    ),
    ErrorSignature(
        name="git_auth",
        root_cause="GIT_AUTH_ERROR",
        keywords=[
            "authentication failed",
            "permission denied (publickey)",
            "could not read from remote repository"
        ],
        confidence=0.65,
        domain="git"
    ),
    ErrorSignature(
        name="git_repo",
        root_cause="GIT_REPO_ERROR",
        keywords=[
            "repository not found",
            "fatal: repository"
        ],
        confidence=0.65,
        domain="git"
    ),
    ErrorSignature(
        name="permission_denied",
        root_cause="PERMISSION_ERROR",
        keywords=[
            "permission denied",
            "access denied",
            "unauthorized",
            "accessdeniedexception"
        ],
        confidence=0.7
    ),
    ErrorSignature(
        name="network_timeout",
        root_cause="NETWORK_ERROR",
        keywords=[
            "timeout",
            "i/o timeout",
            "connection refused",
            "network is unreachable",
            "dial tcp",
            "context deadline exceeded"
        ],
        confidence=0.7
    ),
    ErrorSignature(
        name="command_not_found",
        root_cause="SCRIPT_ERROR",
        keywords=["command not found"],
        confidence=0.6
    ),
]

DOMAIN_HINTS: Dict[str, List[str]] = {
    "kubernetes": [
        "Image pull errors often indicate missing tags, registry auth issues, or network egress blocks.",
        "CrashLoopBackOff usually points to application startup failures or misconfigured env/args.",
        "Probe failures typically mean the app is unhealthy or the probe path/port is wrong.",
        "Volume mount errors suggest missing PVCs, wrong storage class, or node attach limits.",
        "Scheduling failures point to resource pressure, taints/tolerations, or missing node selectors."
    ],
    "terraform": [
        "Auth errors commonly stem from expired credentials, missing roles, or invalid profiles.",
        "State lock errors indicate another run is holding the lock or a stale lock was left behind.",
        "Provider errors often arise from incompatible provider versions or API timeouts.",
        "Validation errors usually mean invalid variables, unknown attributes, or syntax issues.",
        "Apply errors can be caused by cloud-side quotas, missing permissions, or dependency ordering."
    ],
    "ansible": [
        "Unreachable errors typically indicate SSH connectivity, firewall, or DNS issues.",
        "Authentication failures often come from wrong SSH keys, user, or sudo configuration.",
        "Task failures indicate module errors or unmet preconditions on the target host.",
        "Syntax errors suggest malformed YAML or invalid Jinja templating."
    ],
}

DOMAIN_FALLBACKS: Dict[str, Tuple[str, float]] = {
    "kubernetes": ("KUBERNETES_ERROR", 0.45),
    "terraform": ("TERRAFORM_ERROR", 0.45),
    "ansible": ("ANSIBLE_ERROR", 0.45),
    "git": ("GIT_ERROR", 0.45),
    "container": ("CONTAINER_ERROR", 0.45),
    "package": ("DEPENDENCY_ERROR", 0.45),
}

ROOT_CAUSE_DOMAIN_PREFIXES: List[Tuple[str, str]] = [
    ("K8S_", "kubernetes"),
    ("TERRAFORM_", "terraform"),
    ("ANSIBLE_", "ansible"),
    ("GIT_", "git"),
    ("PROMETHEUS_", "prometheus"),
    ("LOKI_", "loki"),
    ("GRAFANA_", "grafana"),
]


def infer_domain(root_cause: Optional[str], origin_step: Optional[str], failure_surface: Optional[str]) -> Optional[str]:
    if root_cause:
        for prefix, domain in ROOT_CAUSE_DOMAIN_PREFIXES:
            if root_cause.startswith(prefix):
                return domain

    for step in (origin_step, failure_surface):
        if step and step in STEP_DOMAIN_MAP:
            return STEP_DOMAIN_MAP[step]

    return None
