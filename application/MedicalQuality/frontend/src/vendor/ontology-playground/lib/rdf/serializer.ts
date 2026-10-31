import type { Ontology, DataBinding } from '../../data/ontology';

/**
 * Escape XML special characters in a string.
 */
export function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

const XSD_TYPE_MAP: Record<string, string> = {
  string: 'xsd:string',
  integer: 'xsd:integer',
  decimal: 'xsd:decimal',
  double: 'xsd:double',
  date: 'xsd:date',
  datetime: 'xsd:dateTime',
  boolean: 'xsd:boolean',
  enum: 'xsd:string',
};

/**
 * Derive a base URI from an ontology name.
 * Strips characters that are invalid in XML/URI contexts.
 */
export function deriveBaseUri(ontologyName: string): string {
  const slug = ontologyName
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  return `http://example.org/ontology/${slug || 'unnamed'}/`;
}

/**
 * Serialize an Ontology (and optional DataBindings) to RDF/XML (OWL).
 */
export function serializeToRDF(
  ontology: Ontology,
  bindings: DataBinding[] = [],
): string {
  const baseUri = deriveBaseUri(ontology.name);
  const entityUris = new Map(ontology.entityTypes.map(e => [e.id, e.iri || baseUri + capitalize(e.id)]));
  const entityUri = (id: string) => escapeXml(entityUris.get(id) || baseUri + capitalize(id));
  const subclassParents = new Map<string, string[]>();
  for (const relationship of ontology.relationships) {
    if (relationship.kind !== 'subclass') continue;
    const parents = subclassParents.get(relationship.from) ?? [];
    parents.push(relationship.to);
    subclassParents.set(relationship.from, parents);
  }

  let rdf = '';

  // XML declaration
  rdf += '<?xml version="1.0" encoding="UTF-8"?>\n';

  // RDF root element with namespace declarations
  rdf += '<rdf:RDF\n';
  rdf += `    xml:base="${baseUri}"\n`;
  rdf += '    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n';
  rdf += '    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"\n';
  rdf += '    xmlns:owl="http://www.w3.org/2002/07/owl#"\n';
  rdf += '    xmlns:xsd="http://www.w3.org/2001/XMLSchema#"\n';
  rdf += `    xmlns:ont="${baseUri}">\n\n`;

  // Ontology declaration
  rdf += `    <owl:Ontology rdf:about="${escapeXml(ontology.iri || baseUri)}">\n`;
  rdf += `        <rdfs:label>${escapeXml(ontology.name)}</rdfs:label>\n`;
  if (ontology.description) {
    rdf += `        <rdfs:comment>${escapeXml(ontology.description)}</rdfs:comment>\n`;
  }
  rdf += '    </owl:Ontology>\n\n';

  // Entity Types as OWL Classes
  rdf += '    <!-- ===================== -->\n';
  rdf += '    <!-- Entity Types (Classes) -->\n';
  rdf += '    <!-- ===================== -->\n\n';

  for (const entity of ontology.entityTypes) {
    rdf += `    <owl:Class rdf:about="${entityUri(entity.id)}">\n`;
    rdf += `        <rdfs:label>${escapeXml(entity.name)}</rdfs:label>\n`;
    if (entity.description) {
      rdf += `        <rdfs:comment>${escapeXml(entity.description)}</rdfs:comment>\n`;
    }
    for (const parentId of subclassParents.get(entity.id) ?? []) {
      rdf += `        <rdfs:subClassOf rdf:resource="${entityUri(parentId)}"/>\n`;
    }
    // Store icon and color as custom annotations
    rdf += `        <ont:icon>${escapeXml(entity.icon)}</ont:icon>\n`;
    rdf += `        <ont:color>${escapeXml(entity.color)}</ont:color>\n`;
    rdf += '    </owl:Class>\n\n';
  }

  // Data Properties (entity properties)
  rdf += '    <!-- ================ -->\n';
  rdf += '    <!-- Data Properties -->\n';
  rdf += '    <!-- ================ -->\n\n';

  for (const entity of ontology.entityTypes) {

    for (const prop of entity.properties) {
      const propName = `${entity.id}_${prop.name}`;
      const xsdType = XSD_TYPE_MAP[prop.type] || 'xsd:string';
      const xsdLocalName = xsdType.split(':')[1];

      rdf += `    <owl:DatatypeProperty rdf:about="${escapeXml(prop.iri || baseUri + propName)}">\n`;
      rdf += `        <rdfs:label>${escapeXml(prop.name)}</rdfs:label>\n`;
      rdf += `        <rdfs:domain rdf:resource="${entityUri(entity.id)}"/>\n`;
      rdf += `        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#${xsdLocalName}"/>\n`;
      if (prop.description) {
        rdf += `        <rdfs:comment>${escapeXml(prop.description)}</rdfs:comment>\n`;
      }
      if (prop.isIdentifier) {
        rdf += '        <ont:isIdentifier rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">true</ont:isIdentifier>\n';
      }
      if (prop.unit) {
        rdf += `        <ont:unit>${escapeXml(prop.unit)}</ont:unit>\n`;
      }
      if (prop.values && prop.values.length > 0) {
        rdf += `        <ont:enumValues>${escapeXml(prop.values.join(','))}</ont:enumValues>\n`;
      }
      // Store the original property type for round-trip fidelity
      rdf += `        <ont:propertyType>${escapeXml(prop.type)}</ont:propertyType>\n`;
      rdf += '    </owl:DatatypeProperty>\n\n';
    }
  }

  // Object Properties (relationships)
  rdf += '    <!-- ================== -->\n';
  rdf += '    <!-- Object Properties -->\n';
  rdf += '    <!-- ================== -->\n\n';

  for (const rel of ontology.relationships) {
    if (rel.kind === 'subclass') continue;

    rdf += `    <owl:ObjectProperty rdf:about="${escapeXml(rel.iri || baseUri + rel.id)}">\n`;
    rdf += `        <rdfs:label>${escapeXml(rel.name)}</rdfs:label>\n`;
    rdf += `        <rdfs:domain rdf:resource="${entityUri(rel.from)}"/>\n`;
    rdf += `        <rdfs:range rdf:resource="${entityUri(rel.to)}"/>\n`;
    if (rel.description) {
      rdf += `        <rdfs:comment>${escapeXml(rel.description)}</rdfs:comment>\n`;
    }
    if (rel.cardinalityKnown !== false) {
      rdf += `        <ont:cardinality>${escapeXml(rel.cardinality)}</ont:cardinality>\n`;
    }
    rdf += `        <ont:fromEntityId>${escapeXml(rel.from)}</ont:fromEntityId>\n`;
    rdf += `        <ont:toEntityId>${escapeXml(rel.to)}</ont:toEntityId>\n`;
    rdf += '    </owl:ObjectProperty>\n\n';

    // Relationship attributes as separate data properties
    if (rel.attributes && rel.attributes.length > 0) {
      for (const attr of rel.attributes) {
        const attrName = `${rel.id}_${attr.name}`;
        rdf += `    <owl:DatatypeProperty rdf:about="${baseUri}${attrName}">\n`;
        rdf += `        <rdfs:label>${escapeXml(attr.name)}</rdfs:label>\n`;
        rdf += `        <rdfs:comment>Relationship attribute for ${escapeXml(rel.name)}</rdfs:comment>\n`;
        rdf += `        <ont:relationshipAttributeOf>${escapeXml(rel.id)}</ont:relationshipAttributeOf>\n`;
        rdf += `        <ont:attributeType>${escapeXml(attr.type)}</ont:attributeType>\n`;
        rdf += '    </owl:DatatypeProperty>\n\n';
      }
    }
  }

  // Data Bindings as structured annotations
  if (bindings.length > 0) {
    rdf += '    <!-- ============= -->\n';
    rdf += '    <!-- Data Bindings -->\n';
    rdf += '    <!-- ============= -->\n\n';

    for (const binding of bindings) {
      rdf += `    <ont:DataBinding rdf:about="${baseUri}binding_${binding.entityTypeId}">\n`;
      rdf += `        <ont:boundClass rdf:resource="${entityUri(binding.entityTypeId)}"/>\n`;
      rdf += `        <ont:boundEntityId>${escapeXml(binding.entityTypeId)}</ont:boundEntityId>\n`;
      rdf += `        <ont:source>${escapeXml(binding.source)}</ont:source>\n`;
      rdf += `        <ont:table>${escapeXml(binding.table)}</ont:table>\n`;
      for (const [propName, colName] of Object.entries(binding.columnMappings)) {
        rdf += `        <ont:columnMapping>${escapeXml(propName)}=${escapeXml(colName)}</ont:columnMapping>\n`;
      }
      rdf += '    </ont:DataBinding>\n\n';
    }
  }

  rdf += '</rdf:RDF>\n';

  return rdf;
}
