from flask import Flask, jsonify, request # Added request
from flask_cors import CORS
import numpy as np
import matplotlib
matplotlib.use('Agg') # IMPORTANT: Use non-interactive backend for server
import matplotlib.pyplot as plt
from matplotlib import cm
import io # To handle image in memory
import base64 # To encode image

# --- Constants from your simulation ---
GRID_SIZE = 100
GRID_MAX = 20
INITIAL_MASS = 10.0 # Will be overridden by request
CLIP_VALUE = -15
SPHERE_X = 12.0
SPHERE_Y = 5.0

# Pre-calculate grid - no need to do this on every request
x = np.linspace(-GRID_MAX, GRID_MAX, GRID_SIZE)
y = np.linspace(-GRID_MAX, GRID_MAX, GRID_SIZE)
X, Y = np.meshgrid(x, y)
R_base = np.sqrt(X**2 + Y**2) + 1e-6 # Base radial distance

# --- Modified Plotting Function ---
def generate_plot_image(mass_value):
    """Generates the 3D plot for a given mass and returns it as a base64 PNG string."""
    
    # Calculate curvature based on input mass
    Z = -mass_value / R_base
    Z_clipped = np.maximum(Z, CLIP_VALUE)
    
    # Create figure and 3D axes IN MEMORY
    fig = plt.figure(figsize=(8, 6)) # Smaller size suitable for web
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot the 3D surface
    surf = ax.plot_surface(X, Y, Z_clipped, cmap=cm.plasma,
                           linewidth=0, antialiased=True, rstride=2, cstride=2) # Reduced stride for performance
    
    # Add the Test Particle (Sphere)
    r_sphere = np.sqrt(SPHERE_X**2 + SPHERE_Y**2) + 1e-6 # Avoid zero division
    z_sphere = -mass_value / r_sphere
    z_sphere_clipped = np.maximum(z_sphere, CLIP_VALUE)
    ax.plot([SPHERE_X], [SPHERE_Y], [z_sphere_clipped], 'o', 
            markersize=8, color='cyan', label='Test Particle')
    
    # Set plot customizations
    ax.set_title(f"Spacetime Curvature (Mass = {mass_value:.1f})")
    ax.set_xlabel("Space (x)")
    ax.set_ylabel("Space (y)")
    ax.set_zlabel("Curvature (z)")
    ax.set_zlim(CLIP_VALUE, 5)
    ax.legend()

    # --- Save plot to a bytes buffer ---
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight') # Save as PNG in memory
    buf.seek(0)
    
    # Encode the image bytes to base64 string
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    # Close the plot figure to free memory
    plt.close(fig)
    
    # Return the base64 string, ready to be embedded in HTML
    return f"data:image/png;base64,{image_base64}"

# -----------------------------------------------------------

# Initialize Flask App
app = Flask(__name__)
CORS(app) 

# Define the API route - now accepts a 'mass' query parameter
@app.route('/run-simulation', methods=['GET'])
def simulation_endpoint():
    try:
        # Get mass value from the URL query string (e.g., ?mass=10)
        # Default to INITIAL_MASS if not provided
        mass = request.args.get('mass', default=INITIAL_MASS, type=float) 
        
        # Generate the plot image for the requested mass
        image_data = generate_plot_image(mass)
        
        # Return the base64 image data in the JSON response
        return jsonify({
            "status": "success",
            "mass_used": mass,
            "image_data": image_data 
        })
        
    except Exception as e:
        print(f"Error during plot generation: {e}")
        # Log the full traceback for debugging if needed
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# Run the Flask development server
if __name__ == '__main__':
    print("Starting Flask server for simulation...")
    # Make sure matplotlib uses 'Agg' backend BEFORE running the app
    app.run(debug=True, host='127.0.0.1', port=5000)

