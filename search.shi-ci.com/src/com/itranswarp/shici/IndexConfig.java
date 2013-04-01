package com.itranswarp.shici;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import org.apache.lucene.document.Field.Index;
import org.apache.lucene.document.Field.Store;

@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface IndexConfig {

	float boost() default 1.0f;

	Store store() default Store.YES;

	Index index() default Index.ANALYZED;

}
