"""
1. Ingestion Agent: Validates, normalizes, deduplicates, and parses CSV/Excel file uploads.
"""
import io
import hashlib
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class IngestionAgent:
    """Agent responsible for raw transaction file parsing, validation, and normalization."""

    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
    MAX_ROWS = 10000

    def parse_csv_file(self, file_bytes: bytes, filename: str, user_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parse CSV file bytes into clean normalized transaction records.
        """
        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise ValueError("File exceeds maximum size limit of 5MB.")

        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception:
            try:
                df = pd.read_excel(io.BytesIO(file_bytes))
            except Exception as e:
                raise ValueError(f"Could not parse file as CSV or Excel: {str(e)}")

        if len(df) > self.MAX_ROWS:
            raise ValueError(f"File exceeds maximum allowed rows ({self.MAX_ROWS}).")

        # Flexible column mapping normalization
        col_map = self._detect_columns(df)
        
        normalized_records = []
        dedup_hashes = set()
        deduped_count = 0
        uncertain_count = 0

        for idx, row in df.iterrows():
            raw_date = row.get(col_map.get("date", ""))
            raw_desc = row.get(col_map.get("description", ""))
            raw_amount = row.get(col_map.get("amount", ""))
            raw_type = row.get(col_map.get("type", ""))

            # Date parsing
            parsed_date, is_date_uncertain = self._parse_date(raw_date)
            
            # Amount & Type parsing
            parsed_amount, txn_type = self._parse_amount(raw_amount, raw_type)
            
            # Merchant cleaning
            merchant_str, is_merchant_uncertain = self._clean_merchant(str(raw_desc) if pd.notna(raw_desc) else "")

            is_uncertain = is_date_uncertain or is_merchant_uncertain or (parsed_amount is None)

            if parsed_date is None or parsed_amount is None:
                continue

            # Compute SHA-256 deduplication hash
            hash_input = f"{user_id}:{parsed_date}:{parsed_amount:.2f}:{merchant_str.lower()}"
            dedup_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

            if dedup_hash in dedup_hashes:
                deduped_count += 1
                continue
            dedup_hashes.add(dedup_hash)

            if is_uncertain:
                uncertain_count += 1

            record = {
                "transaction_date": parsed_date,
                "description": str(raw_desc) if pd.notna(raw_desc) else "Unknown",
                "normalized_merchant": merchant_str,
                "amount": float(parsed_amount),
                "transaction_type": txn_type,
                "dedup_hash": dedup_hash,
                "is_uncertain": is_uncertain
            }
            normalized_records.append(record)

        stats = {
            "total_rows_parsed": len(df),
            "valid_records": len(normalized_records),
            "deduplicated_count": deduped_count,
            "uncertain_count": uncertain_count
        }

        return normalized_records, stats

    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Auto-detect columns from common bank statement headers."""
        cols = {c.lower().strip(): c for c in df.columns}
        mapping = {}

        # Date column
        for candidate in ["date", "txn date", "transaction date", "value date", "posting date"]:
            if candidate in cols:
                mapping["date"] = cols[candidate]
                break
        if "date" not in mapping:
            # Fallback to first column containing 'date'
            for c_low, c_orig in cols.items():
                if "date" in c_low:
                    mapping["date"] = c_orig
                    break

        # Description / Merchant column
        for candidate in ["description", "narrative", "particulars", "merchant", "details", "remarks", "payee"]:
            if candidate in cols:
                mapping["description"] = cols[candidate]
                break

        # Amount column
        for candidate in ["amount", "txn amount", "transaction amount", "debit", "withdrawal"]:
            if candidate in cols:
                mapping["amount"] = cols[candidate]
                break

        # Type column
        for candidate in ["type", "cr/dr", "drcr", "transaction type"]:
            if candidate in cols:
                mapping["type"] = cols[candidate]
                break

        return mapping

    def _parse_date(self, val: Any) -> Tuple[Optional[str], bool]:
        """Parse ambiguous date string safely without throwing exceptions."""
        if pd.isna(val) or not val:
            return None, True
        
        val_str = str(val).strip()
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y"]:
            try:
                dt = datetime.strptime(val_str, fmt)
                return dt.strftime("%Y-%m-%d"), False
            except ValueError:
                continue
        
        # Try pandas fallback date parser
        try:
            dt = pd.to_datetime(val_str)
            return dt.strftime("%Y-%m-%d"), True
        except Exception:
            return None, True

    def _parse_amount(self, amt_val: Any, type_val: Any) -> Tuple[Optional[float], str]:
        """Parse numeric amount and determine if debit, credit, or refund."""
        if pd.isna(amt_val):
            return None, "debit"
        
        amt_str = str(amt_val).replace("Rs.", "").replace("₹", "").replace(",", "").strip()
        try:
            amt = float(amt_str)
        except ValueError:
            return None, "debit"

        txn_type = "debit"
        if type_val and pd.notna(type_val):
            t_str = str(type_val).lower()
            if "credit" in t_str or "cr" in t_str or "deposit" in t_str:
                txn_type = "credit"
            elif "refund" in t_str:
                txn_type = "refund"

        if amt < 0:
            amt = abs(amt)
            if txn_type == "debit":
                txn_type = "refund"

        return amt, txn_type

    def _clean_merchant(self, desc: str) -> Tuple[str, bool]:
        """Clean noisy merchant descriptions (e.g. SWIGGY*ORDER 8843 -> swiggy)."""
        if not desc or desc.lower() in ["nan", "none", "null"]:
            return "Unknown Merchant", True
        
        clean = desc.upper()
        # Remove common bank transaction prefixes
        for prefix in ["UPI/", "POS/", "IMPS/", "NEFT/", "ACH/", "CARD/"]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):]
        
        # Remove reference numbers / trailing digits
        clean = pd.Series([clean]).str.replace(r'\*\d+|\d{6,}', '', regex=True).iloc[0]
        clean = clean.strip()
        
        if not clean:
            return "Unknown Merchant", True

        return clean, False
