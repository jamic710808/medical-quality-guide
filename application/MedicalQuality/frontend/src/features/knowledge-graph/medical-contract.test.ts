import { describe,it,expect } from 'vitest';
import { parseRDF } from '../../vendor/ontology-playground/lib/rdf/parser';
import { serializeToRDF } from '../../vendor/ontology-playground/lib/rdf/serializer';
import type { Ontology } from '../../vendor/ontology-playground/data/ontology';

describe('醫療原生格式適配的語義保真',()=>{
  const ontology:Ontology={iri:'urn:mq:ontology',name:'醫療質控',description:'工程候選',entityTypes:[
    {id:'EvidenceReference',iri:'urn:mq:ontology:EvidenceReference',name:'證據引用',description:'固定證據身份',icon:'📄',color:'#0088ff',properties:[{name:'recordId',iri:'urn:mq:property:recordId',type:'string',isIdentifier:true}]},
    {id:'SourceVersion',iri:'urn:mq:ontology:SourceVersion',name:'來源版本',description:'固定來源版本',icon:'🗂',color:'#88bb44',properties:[]}
  ],relationships:[{id:'derivedFrom',iri:'urn:mq:ontology:derivedFrom',name:'派生自',from:'EvidenceReference',to:'SourceVersion',cardinality:'many-to-many',cardinalityKnown:false}]};
  it('保留原始 URN、中文名、關係方向、屬性類型，未知基數不生成約束',()=>{
    const xml=serializeToRDF(ontology);
    expect(xml).toContain('rdf:about="urn:mq:ontology:EvidenceReference"');
    expect(xml).toContain('rdf:resource="urn:mq:ontology:SourceVersion"');
    expect(xml).not.toContain('<ont:cardinality>');
    const parsed=parseRDF(xml,true);
    expect(parsed.ontology.iri).toBe('urn:mq:ontology');
    expect(parsed.ontology.entityTypes.map(n=>n.iri)).toContain('urn:mq:ontology:EvidenceReference');
    const node=parsed.ontology.entityTypes.find(n=>n.iri==='urn:mq:ontology:EvidenceReference')!;
    expect(node.name).toBe('證據引用');expect(node.properties[0].iri).toBe('urn:mq:property:recordId');
    expect(parsed.ontology.relationships).toHaveLength(1);
    expect(parsed.ontology.relationships[0].from).toBe(node.id);
    expect(parsed.ontology.relationships[0].cardinalityKnown).toBe(false);
  });
  it('相同顯示名稱不合並不同原始 IRI',()=>{
    const input=structuredClone(ontology);input.entityTypes[1].name=input.entityTypes[0].name;
    const parsed=parseRDF(serializeToRDF(input),true);
    expect(new Set(parsed.ontology.entityTypes.map(n=>n.iri)).size).toBe(2);
  });
});
