// Dashboard Navigation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initializeCharts();
    
    // Setup navigation
    setupNavigation();
    
    // Setup file upload
    setupFileUpload();
});

// Navigation Setup
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and sections
            navLinks.forEach(nav => nav.parentElement.classList.remove('active'));
            contentSections.forEach(section => section.classList.remove('active'));
            
            // Add active class to clicked link
            this.parentElement.classList.add('active');
            
            // Show corresponding section
            const targetId = this.getAttribute('href').substring(1);
            document.getElementById(targetId).classList.add('active');
        });
    });
}

// File Upload Setup
function setupFileUpload() {
    const fileInput = document.getElementById('resumeFile');
    const uploadArea = document.getElementById('uploadArea');
    const analysisResults = document.getElementById('analysisResults');
    
    fileInput.addEventListener('change', function(e) {
        if (this.files.length > 0) {
            const file = this.files[0];
            
            // Validate file type
            const validTypes = ['application/pdf', 'application/msword', 
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            
            if (!validTypes.includes(file.type)) {
                alert('Please upload a PDF or Word document');
                return;
            }
            
            // Validate file size (5MB)
            if (file.size > 5 * 1024 * 1024) {
                alert('File size must be less than 5MB');
                return;
            }
            
            // Show loading state
            uploadArea.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                <h3>Analyzing Resume...</h3>
                <p>This may take a few seconds</p>
            `;
            
            // Simulate API call to Python backend
            simulateResumeAnalysis(file);
        }
    });
    
    // Drag and drop support
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = '#2563eb';
        this.style.backgroundColor = '#f8fafc';
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.borderColor = '#cbd5e1';
        this.style.backgroundColor = 'transparent';
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = '#cbd5e1';
        this.style.backgroundColor = 'transparent';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
}

// Simulate Resume Analysis (Replace with actual API call to Python backend)
function simulateResumeAnalysis(file) {
    setTimeout(() => {
        // Show analysis results
        document.getElementById('uploadArea').style.display = 'none';
        document.getElementById('analysisResults').style.display = 'block';
        
        // In real implementation, you would send the file to Python backend
        // and update the UI with the response
        console.log('File uploaded:', file.name);
        
        // Example of calling Python backend API:
        // analyzeResumeWithPython(file);
    }, 2000);
}

// Example function to call Python backend
async function analyzeResumeWithPython(file) {
    const formData = new FormData();
    formData.append('resume', file);
    
    try {
        const response = await fetch('http://localhost:8000/api/analyze-resume', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            updateResumeAnalysisUI(data);
        } else {
            throw new Error('Analysis failed');
        }
    } catch (error) {
        console.error('Error analyzing resume:', error);
        alert('Failed to analyze resume. Please try again.');
        
        // Reset upload area
        document.getElementById('uploadArea').innerHTML = `
            <i class="fas fa-cloud-upload-alt"></i>
            <h3>Upload Your Resume</h3>
            <p>Supported formats: PDF, DOC, DOCX (Max 5MB)</p>
            <button class="upload-btn" onclick="document.getElementById('resumeFile').click()">
                Choose File
            </button>
        `;
    }
}

// Update UI with analysis results from Python backend
function updateResumeAnalysisUI(data) {
    // Update overall score
    document.getElementById('overallScore').textContent = data.overallScore + '%';
    
    // Update individual scores
    const scoreItems = document.querySelectorAll('.score-item');
    scoreItems[0].querySelector('.score-fill').style.width = data.atsScore + '%';
    scoreItems[0].querySelector('span').textContent = data.atsScore + '%';
    
    scoreItems[1].querySelector('.score-fill').style.width = data.keywordScore + '%';
    scoreItems[1].querySelector('span').textContent = data.keywordScore + '%';
    
    scoreItems[2].querySelector('.score-fill').style.width = data.achievementScore + '%';
    scoreItems[2].querySelector('span').textContent = data.achievementScore + '%';
    
    scoreItems[3].querySelector('.score-fill').style.width = data.readabilityScore + '%';
    scoreItems[3].querySelector('span').textContent = data.readabilityScore + '%';
    
    // Update suggestions (you would dynamically generate this based on data.suggestions)
}

// Initialize Charts
function initializeCharts() {
    // Skill Radar Chart
    const skillCtx = document.getElementById('skillRadarChart').getContext('2d');
    const skillChart = new Chart(skillCtx, {
        type: 'radar',
        data: {
            labels: ['JavaScript', 'React', 'Node.js', 'Python', 'SQL', 'Data Structures'],
            datasets: [{
                label: 'Current Level',
                data: [80, 70, 60, 85, 75, 65],
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(59, 130, 246, 1)'
            }, {
                label: 'Target Level',
                data: [90, 85, 80, 90, 85, 85],
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                borderColor: 'rgba(16, 185, 129, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(16, 185, 129, 1)'
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
    
    // Progress Line Chart
    const progressCtx = document.getElementById('progressChart').getContext('2d');
    const progressChart = new Chart(progressCtx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Overall Readiness',
                data: [45, 52, 58, 65, 70, 75],
                borderColor: 'rgba(59, 130, 246, 1)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Resume Score',
                data: [50, 58, 62, 70, 76, 82],
                borderColor: 'rgba(16, 185, 129, 1)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// API Service Functions for Python Backend Integration
const apiService = {
    // Analyze resume with Python backend
    analyzeResume: async (file) => {
        const formData = new FormData();
        formData.append('resume', file);
        
        const response = await fetch('http://localhost:8000/api/analyze-resume', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Resume analysis failed');
        }
        
        return await response.json();
    },
    
    // Get student progress data
    getStudentProgress: async (studentId) => {
        const response = await fetch(`http://localhost:8000/api/student/${studentId}/progress`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch progress data');
        }
        
        return await response.json();
    },
    
    // Submit test scores
    submitTestScores: async (scores) => {
        const response = await fetch('http://localhost:8000/api/test-scores', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scores)
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit test scores');
        }
        
        return await response.json();
    },
    
    // Get certifications
    getCertifications: async (studentId) => {
        const response = await fetch(`http://localhost:8000/api/student/${studentId}/certifications`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch certifications');
        }
        
        return await response.json();
    }
};

// Utility Functions
const utils = {
    // Format percentage
    formatPercentage: (value) => {
        return Math.round(value) + '%';
    },
    
    // Calculate trend
    calculateTrend: (current, previous) => {
        const change = ((current - previous) / previous) * 100;
        return {
            value: Math.abs(Math.round(change)),
            direction: change >= 0 ? 'positive' : 'negative'
        };
    },
    
    // Debounce function for search inputs
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Export for use in other modules (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { apiService, utils };
}