#ifndef LINSOLVERRESULT
#define LINSOLVERRESULT
    
#include "util.hpp"
    
    
class LinSolverResult {
    public:

        int NF;
    
        std::vector<XVec > disp;
        std::vector<XVec > strain;
        std::vector<XVec > lamb;
    
        std::vector<XVec > ostrain;
        std::vector<XVec > ostress;
    
        std::vector<XVec > affine_strain;
        std::vector<XVec > affine_stress;
    
        std::vector<XVec > olambda;
    
        std::vector<double> energy;
    
        bool success;
        std::string msg;
    
    
        double update_det;
    
    
        XVec meas;
        XMat meas_grad;
    
        std::vector<XMat > disp_grad;
    
        std::vector<XVec > current;
        std::vector<XMat > current_grad;
    
        LinSolverResult(int NF) {
            this->NF = NF;
            disp.resize(NF);
            strain.resize(NF);
            lamb.resize(NF);
            
            ostrain.resize(NF);
            ostress.resize(NF);
            
            affine_strain.resize(NF);
            affine_stress.resize(NF);
            
            olambda.resize(NF);
            
            energy.resize(NF);
            
            success = true;
            msg = "initialized";
            
            disp_grad.resize(NF);
            
            current.resize(NF);
            current_grad.resize(NF);
        }
    
        
}; 

#endif // LINSOLVERRESULT