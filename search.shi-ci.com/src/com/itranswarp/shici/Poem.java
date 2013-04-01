package com.itranswarp.shici;

import java.util.LinkedList;
import java.util.List;

import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.Field.Index;
import org.apache.lucene.search.BooleanClause.Occur;

public class Poem {

	@IndexConfig(index=Index.NOT_ANALYZED)
	public String id;

	@IndexConfig(index=Index.NOT_ANALYZED)
	public String poet_id;

	@IndexConfig(boost=2)
	public String poet_name;

	@IndexConfig(boost=2)
	public String poet_name_cht;

	@IndexConfig(index=Index.NO)
	public String poet_name_pinyin;

	@IndexConfig(index=Index.NOT_ANALYZED)
	public String dynasty_id;

	@IndexConfig(index=Index.NO)
	public String dynasty_name;

	@IndexConfig(index=Index.NO)
	public String dynasty_name_cht;

	@IndexConfig(index=Index.NOT_ANALYZED)
	public String form;

	@IndexConfig(boost=2)
	public String name;

	@IndexConfig(boost=2)
	public String name_cht;

	@IndexConfig(index=Index.NO)
	public String name_pinyin;

	@IndexConfig
	public String content;

	@IndexConfig
	public String content_cht;

	@IndexConfig(index=Index.NO)
	public String content_pinyin;

	@IndexConfig(index=Index.NO)
	public String version;

	static final DocConfig[] DOC_CONFIGS;
	static final String[] SEARCH_FIELDS;
	static final Occur[] SEARCH_OCCURS;

	static {
		List<DocConfig> list = new LinkedList<DocConfig>();
		List<String> searchList = new LinkedList<String>();
		for (java.lang.reflect.Field f : Poem.class.getFields()) {
			IndexConfig ic = f.getAnnotation(IndexConfig.class);
			if (ic!=null) {
				list.add(new DocConfig(f, ic));
				if (ic.index()==Index.ANALYZED)
					searchList.add(f.getName());
			}
		}
		DOC_CONFIGS = list.toArray(new DocConfig[list.size()]);
		SEARCH_FIELDS = searchList.toArray(new String[searchList.size()]);
		SEARCH_OCCURS = new Occur[SEARCH_FIELDS.length];
		for (int i=0; i<SEARCH_OCCURS.length; i++)
			SEARCH_OCCURS[i] = Occur.SHOULD;
	}

	public Document toDocument() throws IllegalArgumentException, IllegalAccessException {
		Document doc = new Document();
		for (DocConfig dc : DOC_CONFIGS) {
			doc.add(dc.createField(this));
		}
		return doc;
	}

	public static Poem fromDocument(Document doc) throws IllegalArgumentException, IllegalAccessException {
		Poem p = new Poem();
		for (DocConfig dc : DOC_CONFIGS) {
			dc.setFields(p, doc);
		}
		return p;
	}
}

class DocConfig {
	public DocConfig(java.lang.reflect.Field field, IndexConfig config) {
		this.field = field;
		this.config = config;
	}

	final java.lang.reflect.Field field;
	final IndexConfig config;

	Field createField(Poem p) throws IllegalArgumentException, IllegalAccessException {
		Field f = new Field(field.getName(), field.get(p).toString(), config.store(), config.index());
		f.setBoost(config.boost());
		return f;
	}

	void setFields(Poem p, Document doc) throws IllegalArgumentException, IllegalAccessException {
		field.set(p, doc.get(field.getName()));
	}

}
