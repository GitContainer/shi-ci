package com.itranswarp.shici;

/**
 * Search result with poems, total and next.
 * 
 * @author michael
 */
public class SearchResult {

	public final int total;
	public final String next;
	public final Poem[] poems;

	public SearchResult(int total, String next, Poem[] poems) {
		this.total = total;
		this.next = next;
		this.poems = poems;
	}

	public static final SearchResult EMPTY = new SearchResult(0, null, null);

}
