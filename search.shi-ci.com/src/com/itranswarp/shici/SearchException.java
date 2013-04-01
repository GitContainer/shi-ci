package com.itranswarp.shici;

public class SearchException extends RuntimeException {

	String error;

	public SearchException(String error) {
		this.error = error;
	}

	public SearchException(String error, String message) {
		super(message);
		this.error = error;
	}

	public SearchException(String error, Throwable cause) {
		super(cause);
		this.error = error;
	}

	public SearchException(String error, String message, Throwable cause) {
		super(message, cause);
		this.error = error;
	}

	public String toJsonString() {
		return "{\"error\":\"" + error + "\"}";
	}
}
