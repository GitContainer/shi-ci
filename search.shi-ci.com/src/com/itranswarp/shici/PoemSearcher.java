package com.itranswarp.shici;

import java.io.File;
import java.io.IOException;
import java.util.Map;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.CorruptIndexException;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.queryParser.ParseException;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.Filter;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.PhraseQuery;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.search.TermsFilter;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.search.BooleanClause.Occur;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.store.LockObtainFailedException;
import org.apache.lucene.util.Version;

public class PoemSearcher {

	static final Log log = LogFactory.getLog(PoemSearcher.class);

	Directory directory;
	IndexWriter indexWriter;
	IndexSearcher indexSearcher;
	Analyzer indexAnalyzer;
	long searcherVersion = 0;
	long modifierVersion = 0;

	public PoemSearcher(String path) {
		File f = new File(path);
		if (! f.isDirectory())
			f.mkdirs();
		if (! f.isDirectory())
			throw new SearchException("invalid-index-path: " + path);
		if (! f.canRead())
			throw new SearchException("cannot-read-index: " + path);
		if (! f.canWrite())
			throw new SearchException("cannot-write-index: " + path);
		try {
			directory = FSDirectory.open(f);
		}
		catch (IOException e) {
			throw new SearchException("IOException", e);
		}
		checkIndex();
    	this.indexAnalyzer = new StandardAnalyzer(Version.LUCENE_36);
    	this.indexWriter = openIndexWriter();
	}

	public synchronized void shutdown() {
		close(this.indexWriter);
		close(this.indexSearcher);
	}

	ScoreDoc decodeDoc(String b64next) throws IOException {
		if (b64next==null || b64next.isEmpty())
			return null;
		String s = Utils.b64decode(b64next);
		String[] ss = s.split("\\|");
		if (ss.length!=2)
			return null;
		try {
			int afterDoc = Integer.parseInt(ss[0]);
			float afterScore = Float.parseFloat(ss[1]);
			return new ScoreDoc(afterDoc, afterScore);
		}
		catch (NumberFormatException e) {
			return null;
		}
	}

	String encodeDoc(ScoreDoc scoreDoc) throws IOException {
		if (scoreDoc==null)
			return null;
		String s = scoreDoc.doc + "|" + scoreDoc.score;
		return Utils.b64encode(s);
	}

	public SearchResult search(String[] qs, int maxKeywords, Map<String, String> map, String after, int max) throws Exception {
		Query query = buildQuery(qs, maxKeywords);
		Filter filter = buildFilter(map);
		openIndexSearcher();
		ScoreDoc afterDoc = decodeDoc(after);
		TopDocs topDocs = afterDoc==null ? indexSearcher.search(query, filter, max + 1) : indexSearcher.searchAfter(afterDoc, query, filter, max + 1);
		int total = topDocs.totalHits;
		ScoreDoc[] docs = topDocs.scoreDocs;
		if (docs.length==0) {
			return SearchResult.EMPTY;
		}
		ScoreDoc nextDoc = docs.length > max ? docs[max-1] : null;
		int len = nextDoc==null ? docs.length : max;
		Poem[] results = new Poem[len];
		for (int i=0; i<len; i++) {
			Document doc = indexSearcher.doc(docs[i].doc);
			results[i] = Poem.fromDocument(doc);
		}
		return new SearchResult(total, encodeDoc(nextDoc), results);
	}

	Filter buildFilter(Map<String, String> map) {
		if (map==null || map.isEmpty())
			return null;
		TermsFilter tf = new TermsFilter();
		for (String key : map.keySet()) {
    		tf.addTerm(new Term(key, map.get(key)));
		}
		return tf;
	}

	Query buildQuery(String[] qs, int maxKeywords) throws ParseException {
		if (maxKeywords==1)
            return createMultiFieldsQuery(qs[0]);
        BooleanQuery q = new BooleanQuery();
        for (int i=0; i<maxKeywords; i++) {
        	q.add(createMultiFieldsQuery(qs[i]), Occur.MUST);
        }
        return q;
	}

    Query createMultiFieldsQuery(String q) throws ParseException {
		if (q.length()==1) {
			BooleanQuery bq = new BooleanQuery();
			for (String f : Poem.SEARCH_FIELDS)
				bq.add(new TermQuery(new Term(f, q)), Occur.SHOULD);
			return bq;
		}
		else {
			BooleanQuery bq = new BooleanQuery();
			for (String f : Poem.SEARCH_FIELDS)
				bq.add(createPhraseQuery(f, q), Occur.SHOULD);
			return bq;
		}
	}

	Query createPhraseQuery(String f, String q) {
		PhraseQuery pq = new PhraseQuery();
		int max = q.length();
		if (max > 7)
			max = 7;
		for (int i=0; i<max; i++)
			pq.add(new Term(f, q.substring(i, i+1)));
		return pq;
	}

	IndexSearcher openIndexSearcher() {
        IndexSearcher current = this.indexSearcher;
        if (current != null && searcherVersion == modifierVersion)
            return current;
        try {
        	this.indexSearcher = new IndexSearcher(IndexReader.open(directory));
        	searcherVersion = modifierVersion;
        }
        catch (CorruptIndexException e) {
            throw new SearchException("corrupt-index", e);
        }
        catch (LockObtainFailedException e) {
            throw new SearchException("lock-index-failed", e);
        }
        catch (IOException e) {
            throw new SearchException("io-failed", e);
        }
        close(current);
        return this.indexSearcher;
    }

    public synchronized void index(Poem p) {
        try {
            indexWriter.addDocument(p.toDocument(), indexAnalyzer);
            indexWriter.commit();
        }
        catch (CorruptIndexException e) {
            log.error("Index failed.", e);
            throw new SearchException("index-failed:CorruptIndexException", e);
        }
        catch (LockObtainFailedException e) {
            log.error("Index failed.", e);
            throw new SearchException("index-failed:LockObtainFailedException", e);
        }
        catch (IOException e) {
            log.error("Index failed.", e);
            throw new SearchException("index-failed:IOException", e);
        }
        catch (IllegalArgumentException e) {
        	throw new SearchException("IllegalArgumentException", e);
		}
        catch (IllegalAccessException e) {
			throw new SearchException("IllegalAccessException", e);
		}
        finally {
            modifierVersion++;
        }
    }

    public synchronized void unindex(String poemId) {
        try {
            indexWriter.deleteDocuments(new Term("id", poemId));
            indexWriter.commit();
        }
        catch (CorruptIndexException e) {
            log.error("Index failed.", e);
            throw new SearchException("unindex-failed:CorruptIndexException", e);
        }
        catch (LockObtainFailedException e) {
            log.error("Index failed.", e);
            throw new SearchException("unindex-failed:LockObtainFailedException", e);
        }
        catch (IOException e) {
            log.error("Index failed.", e);
            throw new SearchException("unindex-failed:IOException", e);
        }
        finally {
            modifierVersion++;
        }
    }

    public IndexWriter openIndexWriter() {
    	return openIndexWriter(false);
    }

	synchronized IndexWriter openIndexWriter(boolean createIndex) {
    	IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_36, indexAnalyzer);
    	config.setOpenMode(createIndex ? IndexWriterConfig.OpenMode.CREATE : IndexWriterConfig.OpenMode.APPEND);
        try {
    		return new IndexWriter(directory, config);
        }
        catch (CorruptIndexException e) {
            throw new SearchException("CorruptIndexException", e);
        }
        catch (LockObtainFailedException e) {
            throw new SearchException("LockObtainFailedException", e);
        }
        catch (IOException e) {
            throw new SearchException("IOException", e);
        }
    }

    IndexSearcher close(IndexSearcher i) {
		if (i!=null) {
			try {
                i.close();
            }
			catch (CorruptIndexException e) {
                log.warn("close IndexSearcher failed.", e);
            }
			catch (IOException e) {
                log.warn("close IndexSearcher failed.", e);
            }
		}
		return null;
    }

	IndexWriter close(IndexWriter i) {
		if (i!=null) {
			try {
                i.close();
            }
			catch (CorruptIndexException e) {
                log.warn("close IndexWriter failed.", e);
            }
			catch (IOException e) {
                log.warn("close IndexWriter failed.", e);
            }
		}
		return null;
	}

	void checkIndex() {
        // check index:
        try {
            if (!IndexReader.indexExists(directory)) {
                log.info("Index is not exist. Try to create an EMPTY index.");
                openIndexWriter(true).close();
            }
            if (IndexWriter.isLocked(directory)) {
                log.warn("Directory is locked! Try unlock!");
                IndexWriter.unlock(directory);
            }
        }
        catch (CorruptIndexException e) {
            log.error("Check index failed.", e);
            throw new SearchException("CorruptIndexException", e);
        }
        catch (LockObtainFailedException e) {
            log.error("Check index failed.", e);
            throw new SearchException("LockObtainFailedException", e);
        }
        catch (IOException e) {
            log.error("Check index failed.", e);
            throw new SearchException("IOException", e);
        }
    }

}
