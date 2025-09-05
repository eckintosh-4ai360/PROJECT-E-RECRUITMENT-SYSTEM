# Enhanced Work Experience Analyzer
# Extracts and calculates accurate work experience from resumes using industry standards

import re
import logging
from datetime import datetime, timedelta
from dateutil import parser
from collections import defaultdict
import calendar

# Setup logging
logger = logging.getLogger(__name__)

class WorkExperienceAnalyzer:
    """
    Enhanced work experience extraction that properly parses dates and calculates
    total experience based on industry standards.
    """
    
    def __init__(self):
        self.month_mapping = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
            'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        # Common date range patterns
        self.date_range_patterns = [
            # January 2020 - March 2023, Jan 2020 - Present
            r'(\w+\s+\d{4})\s*(?:to|-|–|—)\s*(\w+\s+\d{4}|present|current)',
            # 01/2020 - 03/2023, 01/2020 - Present
            r'(\d{1,2}/\d{4})\s*(?:to|-|–|—)\s*(\d{1,2}/\d{4}|present|current)',
            # 2020 - 2023, 2020 - Present
            r'(\d{4})\s*(?:to|-|–|—)\s*(\d{4}|present|current)',
            # Jan 2020 to Mar 2023
            r'(\w+\s+\d{4})\s+to\s+(\w+\s+\d{4})',
            # 2020-2023 (with dash)
            r'(\d{4})\s*-\s*(\d{4})',
        ]
        
        # Job title indicators
        self.job_title_keywords = [
            'software engineer', 'developer', 'programmer', 'analyst', 'manager',
            'consultant', 'specialist', 'coordinator', 'assistant', 'intern',
            'associate', 'senior', 'junior', 'lead', 'principal', 'director',
            'technician', 'administrator', 'architect', 'designer', 'data scientist',
            'product manager', 'project manager', 'team lead', 'tech lead',
            'full stack', 'front end', 'backend', 'devops', 'qa engineer',
            'quality assurance', 'business analyst', 'system administrator',
            'network administrator', 'database administrator', 'web developer',
            'mobile developer', 'ui designer', 'ux designer', 'scrum master'
        ]
        
        # Experience section indicators
        self.experience_sections = [
            'work experience', 'professional experience', 'employment history',
            'career history', 'work history', 'employment', 'experience',
            'professional background', 'career summary', 'job experience'
        ]
        
        # Company name indicators
        self.company_indicators = [
            'inc', 'corp', 'corporation', 'company', 'ltd', 'limited', 'llc',
            'technologies', 'systems', 'solutions', 'services', 'consulting',
            'enterprises', 'group', 'holdings', 'international', 'global'
        ]

    def extract_work_experience(self, text):
        """
        Main method to extract and calculate work experience from resume text.
        
        Args:
            text (str): Resume text
            
        Returns:
            dict: Comprehensive work experience analysis
        """
        logger.info("Starting enhanced work experience extraction")
        
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            
            # Find experience section
            experience_section = self._find_experience_section(cleaned_text)
            
            # Extract individual work entries
            work_entries = self._extract_work_entries(experience_section or cleaned_text)
            
            # Parse dates from each entry
            parsed_experiences = []
            for entry in work_entries:
                parsed_entry = self._parse_work_entry(entry)
                if parsed_entry:
                    parsed_experiences.extend(parsed_entry)
            
            # If no structured entries found, try global extraction
            if not parsed_experiences:
                logger.info("No structured entries found, trying global extraction")
                parsed_experiences = self._global_date_extraction(cleaned_text)
            
            # Calculate total experience
            if parsed_experiences:
                total_experience = self._calculate_total_experience(parsed_experiences)
            else:
                # Fallback to simple pattern matching
                logger.info("Date parsing failed, using fallback method")
                total_experience = self._fallback_experience_extraction(text)
            
            return total_experience
            
        except Exception as e:
            logger.error(f"Error in work experience extraction: {e}")
            return self._fallback_experience_extraction(text)

    def _clean_text(self, text):
        """Clean and normalize text for better parsing."""
        if not text:
            return ""
        
        # Normalize whitespace and line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()

    def _find_experience_section(self, text):
        """Find the work experience section in the resume."""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check if this line is an experience section header
            for section_name in self.experience_sections:
                if section_name in line_lower and len(line_lower) < 60:
                    logger.info(f"Found experience section: {line.strip()}")
                    
                    # Find the end of this section (usually at next major section)
                    section_end = len(lines)
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].lower().strip()
                        if any(header in next_line for header in ['education', 'skills', 'projects', 'certifications']) and len(next_line) < 30:
                            section_end = j
                            break
                    
                    return '\n'.join(lines[i:section_end])
        
        return None

    def _extract_work_entries(self, text):
        """Extract individual work experience entries."""
        entries = []
        lines = text.split('\n')
        current_entry = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new work entry (contains job title or company)
            is_new_entry = self._is_job_title_line(line) or self._is_company_line(line)
            
            if is_new_entry and current_entry:
                # Save current entry and start new one
                entries.append('\n'.join(current_entry))
                current_entry = [line]
            else:
                current_entry.append(line)
        
        # Add the last entry
        if current_entry:
            entries.append('\n'.join(current_entry))
        
        # Filter out very short entries (likely not work experience)
        entries = [entry for entry in entries if len(entry.split()) > 3]
        
        logger.info(f"Extracted {len(entries)} work entries")
        return entries

    def _is_job_title_line(self, line):
        """Check if line contains a job title."""
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in self.job_title_keywords)

    def _is_company_line(self, line):
        """Check if line contains a company name."""
        line_lower = line.lower()
        
        # Look for company indicators
        has_company_indicator = any(indicator in line_lower for indicator in self.company_indicators)
        
        # Check if line is short enough to be a company name (not a description)
        is_reasonable_length = len(line.split()) <= 8
        
        # Avoid lines that are clearly job descriptions
        is_not_description = not any(word in line_lower for word in ['responsible', 'developed', 'managed', 'created', 'implemented'])
        
        return has_company_indicator and is_reasonable_length and is_not_description

    def _parse_work_entry(self, entry_text):
        """Parse a single work experience entry to extract dates and details."""
        experiences = []
        
        # Look for date ranges in the entry
        for pattern in self.date_range_patterns:
            matches = re.finditer(pattern, entry_text, re.IGNORECASE)
            
            for match in matches:
                start_str = match.group(1).strip()
                end_str = match.group(2).strip()
                
                try:
                    # Parse start date
                    start_date = self._parse_date_string(start_str)
                    
                    # Parse end date
                    if end_str.lower() in ['present', 'current']:
                        end_date = datetime.now()
                        is_current = True
                    else:
                        end_date = self._parse_date_string(end_str)
                        is_current = False
                    
                    if start_date and end_date and start_date <= end_date:
                        experience = {
                            'start_date': start_date,
                            'end_date': end_date,
                            'is_current': is_current,
                            'company': self._extract_company_name(entry_text),
                            'position': self._extract_job_title(entry_text),
                            'duration_months': self._calculate_months_between(start_date, end_date),
                            'raw_text': entry_text[:200] + '...' if len(entry_text) > 200 else entry_text
                        }
                        experiences.append(experience)
                        
                except Exception as e:
                    logger.warning(f"Error parsing dates '{start_str}' to '{end_str}': {e}")
                    continue
        
        return experiences

    def _parse_date_string(self, date_str):
        """Parse various date string formats to datetime object."""
        date_str = date_str.strip().lower()
        
        try:
            # Try dateutil parser first (handles most formats automatically)
            return parser.parse(date_str, fuzzy=True)
        except:
            pass
        
        # Manual parsing for specific formats
        try:
            # Format: "jan 2020" or "january 2020"
            month_year_match = re.match(r'(\w+)\s+(\d{4})', date_str)
            if month_year_match:
                month_str = month_year_match.group(1)
                year = int(month_year_match.group(2))
                
                if month_str in self.month_mapping:
                    month = self.month_mapping[month_str]
                    return datetime(year, month, 1)
            
            # Format: "MM/YYYY" or "MM-YYYY"
            mm_yyyy_match = re.match(r'(\d{1,2})[/-](\d{4})', date_str)
            if mm_yyyy_match:
                month = int(mm_yyyy_match.group(1))
                year = int(mm_yyyy_match.group(2))
                if 1 <= month <= 12:
                    return datetime(year, month, 1)
            
            # Format: "YYYY/MM" or "YYYY-MM"
            yyyy_mm_match = re.match(r'(\d{4})[/-](\d{1,2})', date_str)
            if yyyy_mm_match:
                year = int(yyyy_mm_match.group(1))
                month = int(yyyy_mm_match.group(2))
                if 1 <= month <= 12:
                    return datetime(year, month, 1)
            
            # Format: "YYYY" (year only)
            year_match = re.match(r'^(\d{4})$', date_str)
            if year_match:
                year = int(year_match.group(1))
                if 1950 <= year <= datetime.now().year:
                    return datetime(year, 1, 1)
        
        except Exception as e:
            logger.warning(f"Manual date parsing failed for '{date_str}': {e}")
        
        return None

    def _extract_company_name(self, entry_text):
        """Extract company name from work experience entry."""
        lines = entry_text.split('\n')
        
        for line in lines[:4]:  # Check first few lines
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that are clearly job titles
            if self._is_job_title_line(line):
                continue
            
            # Look for company indicators or assume it's a company if it's a reasonable length
            if (self._is_company_line(line) or 
                (len(line.split()) <= 6 and not any(word in line.lower() for word in ['developed', 'managed', 'responsible']))):
                return line
        
        return "Unknown Company"

    def _extract_job_title(self, entry_text):
        """Extract job title from work experience entry."""
        lines = entry_text.split('\n')
        
        for line in lines[:3]:  # Check first few lines
            line = line.strip()
            if self._is_job_title_line(line):
                return line
        
        return "Unknown Position"

    def _calculate_months_between(self, start_date, end_date):
        """Calculate months between two dates."""
        try:
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            return max(0, months)
        except:
            return 0

    def _global_date_extraction(self, text):
        """Extract dates globally when structured parsing fails."""
        experiences = []
        
        # Find all dates in the text
        all_dates = []
        
        # Pattern for various date formats
        date_patterns = [
            r'\b(\w+\s+\d{4})\b',  # January 2020
            r'\b(\d{1,2}/\d{4})\b',  # 01/2020
            r'\b(\d{4})\b'  # 2020
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                date_str = match.group(1)
                parsed_date = self._parse_date_string(date_str)
                
                if parsed_date and 1990 <= parsed_date.year <= datetime.now().year:
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(text), match.end() + 100)
                    context = text[context_start:context_end]
                    
                    # Check if context suggests work experience
                    if any(keyword in context.lower() for keyword in self.job_title_keywords):
                        all_dates.append({
                            'date': parsed_date,
                            'context': context,
                            'position': match.start()
                        })
        
        # Sort dates and try to pair them
        all_dates.sort(key=lambda x: x['date'])
        
        if len(all_dates) >= 2:
            # Assume first date is start of career, last is end/current
            start_date = all_dates[0]['date']
            end_date = all_dates[-1]['date']
            
            experiences.append({
                'start_date': start_date,
                'end_date': end_date,
                'is_current': end_date.year == datetime.now().year,
                'company': 'Extracted from dates',
                'position': 'Various positions',
                'duration_months': self._calculate_months_between(start_date, end_date),
                'raw_text': 'Global date extraction'
            })
        
        return experiences

    def _fallback_experience_extraction(self, text):
        """Fallback method using simple pattern matching."""
        text_lower = text.lower()
        
        # Look for explicit experience statements
        experience_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*years?\s*(?:in|at|with)',
            r'experience\s*:?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*year\s*(?:of\s*)?experience'
        ]
        
        total_years = 0
        experiences = []
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                years = int(match.group(1))
                total_years = max(total_years, years)
        
        if total_years > 0:
            start_date = datetime.now() - timedelta(days=total_years * 365)
            experiences.append({
                'start_date': start_date,
                'end_date': datetime.now(),
                'is_current': True,
                'company': 'Pattern extraction',
                'position': 'Various positions',
                'duration_months': total_years * 12,
                'raw_text': 'Fallback extraction'
            })
        
        return {
            'total_years': float(total_years),
            'total_months': total_years * 12,
            'experience_level': self._determine_experience_level(total_years),
            'work_experiences': experiences,
            'earliest_start_date': start_date.strftime('%Y-%m-%d') if total_years > 0 else None,
            'latest_end_date': datetime.now().strftime('%Y-%m-%d') if total_years > 0 else None,
            'experience_summary': f"{total_years} years of experience (pattern extraction)",
            'gaps_detected': [],
            'overlaps_detected': [],
            'extraction_method': 'fallback'
        }

    def _calculate_total_experience(self, experiences):
        """Calculate comprehensive work experience statistics."""
        if not experiences:
            return self._fallback_experience_extraction("")
        
        # Sort experiences by start date
        sorted_experiences = sorted(experiences, key=lambda x: x['start_date'])
        
        # Calculate total non-overlapping experience
        total_months = self._calculate_non_overlapping_months(sorted_experiences)
        total_years = total_months / 12
        
        # Detect gaps and overlaps
        gaps = self._detect_employment_gaps(sorted_experiences)
        overlaps = self._detect_overlapping_employment(sorted_experiences)
        
        # Get date range
        earliest_start = sorted_experiences[0]['start_date']
        latest_end = max(exp['end_date'] for exp in sorted_experiences)
        
        # Generate summary
        summary = self._generate_detailed_summary(sorted_experiences, total_years, gaps, overlaps)
        
        return {
            'total_years': round(total_years, 1),
            'total_months': total_months,
            'experience_level': self._determine_experience_level(total_years),
            'work_experiences': sorted_experiences,
            'earliest_start_date': earliest_start.strftime('%Y-%m-%d'),
            'latest_end_date': latest_end.strftime('%Y-%m-%d'),
            'experience_summary': summary,
            'gaps_detected': gaps,
            'overlaps_detected': overlaps,
            'extraction_method': 'structured_parsing',
            'career_timeline': self._create_career_timeline(sorted_experiences)
        }

    def _calculate_non_overlapping_months(self, experiences):
        """Calculate total months of non-overlapping work experience."""
        if not experiences:
            return 0
        
        # Sort by start date
        sorted_exp = sorted(experiences, key=lambda x: x['start_date'])
        
        total_months = 0
        current_end = None
        
        for exp in sorted_exp:
            start_date = exp['start_date']
            end_date = exp['end_date']
            
            if current_end is None or start_date >= current_end:
                # No overlap
                months = self._calculate_months_between(start_date, end_date)
                total_months += months
                current_end = end_date
            else:
                # Overlap detected
                if end_date > current_end:
                    # Add only non-overlapping portion
                    months = self._calculate_months_between(current_end, end_date)
                    total_months += months
                    current_end = end_date
        
        return total_months

    def _detect_employment_gaps(self, experiences):
        """Detect gaps in employment history."""
        gaps = []
        
        if len(experiences) < 2:
            return gaps
        
        sorted_exp = sorted(experiences, key=lambda x: x['start_date'])
        
        for i in range(len(sorted_exp) - 1):
            current_end = sorted_exp[i]['end_date']
            next_start = sorted_exp[i + 1]['start_date']
            
            # Calculate gap in months
            gap_months = self._calculate_months_between(current_end, next_start)
            
            # Consider gaps of 1+ months as significant
            if gap_months > 1:
                gaps.append({
                    'start_date': current_end.strftime('%Y-%m-%d'),
                    'end_date': next_start.strftime('%Y-%m-%d'),
                    'duration_months': gap_months,
                    'after_company': sorted_exp[i]['company'],
                    'before_company': sorted_exp[i + 1]['company']
                })
        
        return gaps

    def _detect_overlapping_employment(self, experiences):
        """Detect overlapping employment periods."""
        overlaps = []
        
        for i, exp1 in enumerate(experiences):
            for j, exp2 in enumerate(experiences[i + 1:], i + 1):
                # Check if there's overlap
                if (exp1['start_date'] < exp2['end_date'] and 
                    exp2['start_date'] < exp1['end_date']):
                    
                    overlap_start = max(exp1['start_date'], exp2['start_date'])
                    overlap_end = min(exp1['end_date'], exp2['end_date'])
                    overlap_months = self._calculate_months_between(overlap_start, overlap_end)
                    
                    if overlap_months > 0:
                        overlaps.append({
                            'company1': exp1['company'],
                            'company2': exp2['company'],
                            'overlap_start': overlap_start.strftime('%Y-%m-%d'),
                            'overlap_end': overlap_end.strftime('%Y-%m-%d'),
                            'overlap_months': overlap_months
                        })
        
        return overlaps

    def _determine_experience_level(self, years):
        """Determine experience level based on years of experience."""
        if years < 1:
            return "entry"
        elif years < 3:
            return "junior"
        elif years < 6:
            return "mid"
        elif years < 10:
            return "senior"
        else:
            return "expert"

    def _generate_detailed_summary(self, experiences, total_years, gaps, overlaps):
        """Generate a comprehensive human-readable summary."""
        summary_parts = []
        
        # Total experience
        if total_years < 1:
            summary_parts.append(f"{round(total_years * 12)} months of total experience")
        else:
            summary_parts.append(f"{total_years:.1f} years of total experience")
        
        # Number of positions
        num_positions = len(experiences)
        if num_positions > 1:
            summary_parts.append(f"across {num_positions} positions")
        
        # Current status
        current_roles = [exp for exp in experiences if exp.get('is_current', False)]
        if current_roles:
            summary_parts.append("currently employed")
        
        # Gaps and overlaps
        if gaps:
            summary_parts.append(f"{len(gaps)} employment gap(s) detected")
        if overlaps:
            summary_parts.append(f"{len(overlaps)} overlapping employment period(s)")
        
        return ", ".join(summary_parts) + "."

    def _create_career_timeline(self, experiences):
        """Create a timeline of career progression."""
        timeline = []
        
        for exp in sorted(experiences, key=lambda x: x['start_date']):
            timeline.append({
                'period': f"{exp['start_date'].strftime('%b %Y')} - {exp['end_date'].strftime('%b %Y') if not exp['is_current'] else 'Present'}",
                'company': exp['company'],
                'position': exp['position'],
                'duration_months': exp['duration_months'],
                'is_current': exp.get('is_current', False)
            })
        
        return timeline


# Convenience function to maintain compatibility with existing code
def extract_work_experience(text):
    """Extract work experience using the enhanced analyzer."""
    analyzer = WorkExperienceAnalyzer()
    return analyzer.extract_work_experience(text)

# Legacy function for backward compatibility
def extract_experience_level(text):
    """Legacy function - redirects to enhanced work experience extraction."""
    result = extract_work_experience(text)
    return {
        "total_years": result["total_years"],
        "experience_level": result["experience_level"],
        "matches": [exp.get('position', 'Unknown') for exp in result.get('work_experiences', [])]
    }
