"""CLI interface using Click - simple and functional."""

import asyncio
import click
from pathlib import Path
from uuid import UUID
import json

from .main import VectorDB


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Vector Database CLI - Simple document storage with embeddings."""
    if verbose:
        import logging
        logging.basicConfig(level=logging.INFO)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
def ingest(file_path: Path):
    """Ingest a single file into the vector database.
    
    Example:
        vector-db ingest document.txt
    """
    try:
        db = VectorDB()
        result = asyncio.run(db.ingest_file(file_path))
        click.echo(f"✅ {result}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('dir_path', type=click.Path(exists=True, path_type=Path))
@click.option('--recursive', '-r', is_flag=True, help='Search subdirectories recursively')
def ingest_dir(dir_path: Path, recursive: bool):
    """Ingest all supported files in a directory.
    
    Example:
        vector-db ingest-dir ./documents --recursive
    """
    try:
        db = VectorDB()
        results = asyncio.run(db.ingest_directory(dir_path, recursive))
        
        success_count = sum(1 for r in results if "Successfully ingested" in r)
        error_count = len(results) - success_count
        
        click.echo(f"📁 Processed {len(results)} files:")
        click.echo(f"   ✅ Success: {success_count}")
        click.echo(f"   ❌ Errors: {error_count}")
        
        if error_count > 0:
            click.echo("\nErrors:")
            for result in results:
                if "Failed" in result:
                    click.echo(f"   • {result}")
                    
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=5, help='Number of results to return')
def search(query: str, limit: int):
    """Search for documents by text content.
    
    Example:
        vector-db search "machine learning" --limit 10
    """
    try:
        db = VectorDB()
        results = db.search_by_text(query, limit)
        
        if not results:
            click.echo(f"🔍 No documents found matching '{query}'")
            return
        
        click.echo(f"🔍 Found {len(results)} documents matching '{query}':")
        click.echo()
        
        for i, doc in enumerate(results, 1):
            click.echo(f"{i}. {doc.filename}")
            click.echo(f"   ID: {doc.id}")
            click.echo(f"   Preview: {doc.content_preview}")
            if doc.embedding_dimension:
                click.echo(f"   Embedding: {doc.embedding_dimension}D vector")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--limit', '-l', default=20, help='Number of documents to show')
@click.option('--offset', '-o', default=0, help='Number of documents to skip')
def list(limit: int, offset: int):
    """List all documents in the database.
    
    Example:
        vector-db list --limit 10
    """
    try:
        db = VectorDB()
        docs = db.list_documents(limit, offset)
        
        if not docs:
            click.echo("📄 No documents found in the database")
            return
        
        click.echo(f"📄 Found {len(docs)} documents:")
        click.echo()
        
        for i, doc in enumerate(docs, offset + 1):
            click.echo(f"{i}. {doc.filename}")
            click.echo(f"   ID: {doc.id}")
            click.echo(f"   Size: {len(doc.content):,} characters")
            if doc.created_at:
                click.echo(f"   Created: {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('doc_id', type=str)
def get(doc_id: str):
    """Get a specific document by ID.
    
    Example:
        vector-db get 123e4567-e89b-12d3-a456-426614174000
    """
    try:
        doc_uuid = UUID(doc_id)
        db = VectorDB()
        doc = db.get_document(doc_uuid)
        
        if not doc:
            click.echo(f"❌ Document not found: {doc_id}")
            return
        
        click.echo(f"📄 Document: {doc.filename}")
        click.echo(f"   ID: {doc.id}")
        click.echo(f"   Size: {len(doc.content):,} characters")
        if doc.created_at:
            click.echo(f"   Created: {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if doc.embedding_dimension:
            click.echo(f"   Embedding: {doc.embedding_dimension}D vector")
        click.echo()
        click.echo("Content preview:")
        click.echo(doc.content_preview)
        
    except ValueError:
        click.echo(f"❌ Invalid UUID format: {doc_id}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('doc_id', type=str)
@click.confirmation_option(prompt='Are you sure you want to delete this document?')
def delete(doc_id: str):
    """Delete a document by ID.
    
    Example:
        vector-db delete 123e4567-e89b-12d3-a456-426614174000
    """
    try:
        doc_uuid = UUID(doc_id)
        db = VectorDB()
        
        # Show document info before deletion
        doc = db.get_document(doc_uuid)
        if not doc:
            click.echo(f"❌ Document not found: {doc_id}")
            return
        
        click.echo(f"Deleting document: {doc.filename}")
        
        success = db.delete_document(doc_uuid)
        if success:
            click.echo(f"✅ Document deleted successfully")
        else:
            click.echo(f"❌ Failed to delete document")
            
    except ValueError:
        click.echo(f"❌ Invalid UUID format: {doc_id}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
def health():
    """Check the health of all services.
    
    Example:
        vector-db health
    """
    try:
        db = VectorDB()
        status = asyncio.run(db.health_check())
        
        click.echo("🏥 Health Check Results:")
        click.echo()
        
        # Ollama status
        ollama_icon = "✅" if status['ollama'] else "❌"
        click.echo(f"   {ollama_icon} Ollama: {'Healthy' if status['ollama'] else 'Unhealthy'}")
        
        # Supabase status
        supabase_icon = "✅" if status['supabase'] else "❌"
        click.echo(f"   {supabase_icon} Supabase: {'Healthy' if status['supabase'] else 'Unhealthy'}")
        
        # Overall status
        overall_icon = "✅" if status['overall'] else "❌"
        click.echo(f"   {overall_icon} Overall: {'All systems operational' if status['overall'] else 'Some systems down'}")
        
        if not status['overall']:
            raise click.Abort()
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
def stats():
    """Show database statistics.
    
    Example:
        vector-db stats
    """
    try:
        db = VectorDB()
        stats = db.get_stats()
        
        if 'error' in stats:
            click.echo(f"❌ Error getting stats: {stats['error']}")
            return
        
        click.echo("📊 Database Statistics:")
        click.echo()
        click.echo(f"   📄 Total documents: {stats['total_documents']:,}")
        click.echo(f"   💾 Total content size: {stats['total_content_size']:,} bytes")
        click.echo(f"   📏 Average document size: {stats['average_document_size']:,} bytes")
        
        if stats['file_types']:
            click.echo()
            click.echo("   📁 File types:")
            for ext, count in sorted(stats['file_types'].items()):
                click.echo(f"      {ext or 'no extension'}: {count}")
        
        click.echo()
        click.echo("   ⚙️  Configuration:")
        click.echo(f"      Chunk size: {stats['config']['chunk_size']}")
        click.echo(f"      Max file size: {stats['config']['max_file_size_mb']}MB")
        click.echo(f"      Supported extensions: {', '.join(stats['config']['supported_extensions'])}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
def config():
    """Show current configuration.
    
    Example:
        vector-db config
    """
    try:
        from .config import get_config
        config = get_config()
        config.print_summary()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()