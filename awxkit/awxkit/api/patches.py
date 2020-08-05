import uuid
import hashlib
import logging

log = logging.getLogger(__name__)


def patch_job_template_organization(resource, namespace):
    """Patch a Unified Job Template natural key missing the organization.

    On less versions of AWX prior to 10.0.0, Workflow Job Template Nodes that
    have an associated Unified Job Template will reference it without
    specifying the Organization in the natural key. This will cause it to not
    be imported correctly, appearing as 'Deleted' in the AWX user interface.

    This function will patch the correct, related organization back into the
    natural key.
    """
    if 'organization' not in namespace:
        if resource.type in ['job_template', 'unified_job_template']:
            if resource['project']:
                related_object = resource.get_related('project')
            elif resource['inventory']:
                related_object = resource.get_related('inventory')
            else:
                log.error(
                    "Could not infer the organization for: " + resource.url
                )
                return

            related_org = related_object.get_related('organization')
            namespace.update(
                {
                    'organization': related_org.get_natural_key()
                }
            )
            log.warning('Patched {}'.format(namespace))


def patch_workflow_node_identifier(resource, namespace):
    """Patch a Workflow Job Template Node namespace missing an identifier.

    Unique identifiers have been introduced in AWX 10.0.0 for resources of
    type 'workflow_job_template_node'. These identifiers are used in the
    node's natural key.

    Exporting these resources from AWX servers prior to 10.0.0 and
    importing them in more recent versions of AWX without a proper identifier
    will cause problems when generating the Workflow node sequence.

    This function will patch the namespace by creating a unique identifier
    based on the numerical id of the API resource that exported.
    """
    if 'identifier' not in namespace:
        identifier = str(uuid.UUID(
            hashlib.md5(str(resource.id).encode()).hexdigest()
        ))
        namespace['identifier'] = identifier


def patch_missing(resource_page, fields_to_export):
    """Patch missing fields in resources exported from previous AWX versions.
    """
    if resource_page.type == "workflow_job_template_node":
        patch_workflow_node_identifier(resource_page, fields_to_export)
